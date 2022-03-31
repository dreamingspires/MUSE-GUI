import os
import warnings
from pathlib import Path
from typing import List, Optional, Tuple

import toml
from muse.mca import MCA

from muse_gui.backend.data.agent import Agent
from muse_gui.backend.data.commodity import Commodity
from muse_gui.backend.data.process import Process
from muse_gui.backend.data.region import Region
from muse_gui.backend.data.run_model import RunModel
from muse_gui.backend.data.sector import Sector
from muse_gui.backend.data.timeslice import AvailableYear, LevelName, Timeslice
from muse_gui.backend.settings import SettingsModel
from muse_gui.backend.settings.global_input_files_model import GlobalInputFiles
from muse_gui.backend.settings.output import Output, Quantity, Sink
from muse_gui.backend.utils import unpack_timeslice

from .agent import AgentDatastore
from .available_year import AvailableYearDatastore
from .commodity import CommodityDatastore
from .exporters import (
    agents_to_dataframe,
    convert_timeslices,
    export_commodities,
    export_projections,
    generate_sectors,
    replace_path_prefix,
)
from .importers import (
    get_agents,
    get_commodities_data,
    get_processes,
    get_sectors,
    path_string_to_dataframe,
)
from .level_name import LevelNameDatastore
from .process import ProcessDatastore
from .region import RegionDatastore
from .sector import SectorDatastore
from .timeslice import TimesliceDatastore


class Datastore:
    _region_datastore: RegionDatastore
    _sector_datastore: SectorDatastore
    _level_name_datastore: LevelNameDatastore
    _available_years_datastore: AvailableYearDatastore
    _timeslice_datastore: TimesliceDatastore
    _commodity_datastore: CommodityDatastore
    _process_datastore: ProcessDatastore
    _agent_datastore: AgentDatastore
    _export_path: Optional[Path]
    run_settings: Optional[RunModel]

    def __init__(
        self,
        regions: List[Region] = [],
        sectors: List[Sector] = [],
        level_names: List[LevelName] = [],
        available_years: List[AvailableYear] = [],
        timeslices: List[Timeslice] = [],
        commodities: List[Commodity] = [],
        processes: List[Process] = [],
        agents: List[Agent] = [],
        run_model: Optional[RunModel] = None,
    ) -> None:
        self._region_datastore = RegionDatastore(self, regions)
        self._sector_datastore = SectorDatastore(self, sectors)
        self._level_name_datastore = LevelNameDatastore(self, level_names)
        self._available_years_datastore = AvailableYearDatastore(self, available_years)
        self._timeslice_datastore = TimesliceDatastore(self, timeslices)
        self._commodity_datastore = CommodityDatastore(self, commodities)
        self._agent_datastore = AgentDatastore(self, agents)
        self._process_datastore = ProcessDatastore(self, processes)
        self.run_settings = run_model
        self._export_path = None

    @property
    def region(self):
        return self._region_datastore

    @property
    def sector(self):
        return self._sector_datastore

    @property
    def level_name(self):
        return self._level_name_datastore

    @property
    def available_year(self):
        return self._available_years_datastore

    @property
    def timeslice(self):
        return self._timeslice_datastore

    @property
    def commodity(self):
        return self._commodity_datastore

    @property
    def process(self):
        return self._process_datastore

    @property
    def agent(self):
        return self._agent_datastore

    def run_muse(
        self, export_path: Optional[str] = None, results_path: Optional[str] = None
    ) -> Tuple[Path, Path]:
        if export_path is None and self._export_path is None:
            export_path_obj = Path("./Output")
        elif export_path is None:
            export_path_obj = self._export_path
        else:
            export_path_obj = Path(export_path)
        export_settings_file, prices_path, capacity_path = self.export_to_folder(
            str(export_path_obj), results_path
        )

        with warnings.catch_warnings():
            warnings.simplefilter(action="ignore", category=FutureWarning)
            my_mca = MCA.factory(export_settings_file)
            my_mca.run()
        return prices_path, capacity_path

    @classmethod
    def from_settings(cls, settings_path: str):
        toml_out = toml.load(settings_path)
        path = Path(settings_path)
        folder = path.parents[0].absolute()
        settings_model = SettingsModel.parse_obj(toml_out)
        global_commodities_data = path_string_to_dataframe(
            folder, Path(settings_model.global_input_files.global_commodities)
        )
        projections_data = path_string_to_dataframe(
            folder, Path(settings_model.global_input_files.projections)
        )
        projections_data_without_unit = projections_data.drop(0)
        unit_row = projections_data.iloc[0]

        regions = projections_data_without_unit["RegionName"].unique()

        region_models = [Region(name=name) for name in regions]

        commodity_models = get_commodities_data(
            global_commodities_data, projections_data_without_unit, unit_row
        )

        year_models = [
            AvailableYear(year=i) for i in projections_data_without_unit["Time"]
        ]

        sector_models = get_sectors(settings_model)

        timeslice_info = unpack_timeslice(settings_model.timeslices)
        level_name_models = [LevelName(level=i) for i in timeslice_info.level_names]
        timeslice_models = [
            Timeslice(name=k, value=v) for k, v in timeslice_info.timeslices.items()
        ]

        agent_models = get_agents(settings_model, folder)
        process_models = get_processes(
            settings_model, folder, commodity_models, agent_models
        )

        return cls(
            regions=region_models,
            available_years=year_models,
            commodities=commodity_models,
            sectors=sector_models,
            level_names=level_name_models,
            timeslices=timeslice_models,
            agents=agent_models,
            processes=process_models,
            run_model=RunModel.parse_obj(toml_out),
        )

    def export_to_folder(
        self, folder_path: str, results_path: Optional[str] = None
    ) -> Tuple[Path, Path, Path]:
        if results_path is None:
            results_path = f"{folder_path}{os.sep}Results"
        folder_path_obj = Path(folder_path)
        self._export_path = folder_path_obj
        if not folder_path_obj.exists():
            folder_path_obj.mkdir(parents=True)
        input_folder = Path(f"{folder_path}{os.sep}input")
        if not input_folder.exists():
            input_folder.mkdir(parents=True)
        technodata_folder = Path(f"{folder_path}{os.sep}technodata")
        if not technodata_folder.exists():
            technodata_folder.mkdir(parents=True)
        commodities_path = Path(f"{str(input_folder)}{os.sep}GlobalCommodities.csv")
        projections_path = Path(f"{str(input_folder)}{os.sep}Projections.csv")
        new_settings_path = Path(f"{folder_path}{os.sep}settings.toml")
        commodity_data = self._commodity_datastore._data

        export_commodities(commodity_data, commodities_path)

        export_projections(self, commodity_data, projections_path)

        # generate agents file
        agents_df = agents_to_dataframe(list(self._agent_datastore._data.values()))
        agents_path = Path(f"{technodata_folder}{os.sep}Agents.csv")
        agents_df.to_csv(agents_path, index=False)

        # Create sector folders:
        new_sectors = generate_sectors(
            self, technodata_folder, folder_path_obj, agents_path
        )

        new_timeslices = convert_timeslices(self)

        assert self.run_settings is not None

        prices_path = Path(results_path + os.sep + "MCAPrices.csv")
        capacity_path = Path(results_path + os.sep + "MCACapacity.csv")
        outputs = [
            Output(
                quantity=Quantity.prices,
                sink=Sink.csv,
                filename=str(prices_path.absolute()),
                overwrite=True,
                keep_columns=None,
                index=True,
            ),
            Output(
                quantity=Quantity.capacity,
                sink=Sink.aggregate,
                filename=str(capacity_path.absolute()),
                overwrite=True,
                keep_columns=[
                    "technology",
                    "region",
                    "agent",
                    "type",
                    "sector",
                    "capacity",
                    "year",
                ],
                index=False,
            ),
        ]

        new_settings_model = SettingsModel(
            **self.run_settings.dict(),
            global_input_files=GlobalInputFiles(
                projections=replace_path_prefix(projections_path, folder_path_obj),
                global_commodities=replace_path_prefix(
                    commodities_path, folder_path_obj
                ),
            ),
            sectors=new_sectors,
            timeslices=new_timeslices,
            outputs=outputs,
        )

        with open(new_settings_path, "w+") as f:
            toml.dump(new_settings_model.dict(), f)
        return new_settings_path, prices_path, capacity_path
