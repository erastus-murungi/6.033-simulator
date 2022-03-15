import concurrent
from concurrent.futures import ProcessPoolExecutor

import matplotlib.pyplot as plt
from battery import INTERVAL, CentralUtilityBattery
from house import *
from link import *
from microgrid import HousesMicrogrid, BuildingsMicrogrid, CriticalMicrogrid


class Controller:
    def __init__(self, graph_periodicity: int = 60 * 60):
        self.locations_clustered = unpickle_clustered_locations()
        self.house_microgrids = tuple(
            HousesMicrogrid(houses) for houses in get_houses(self.locations_clustered)
        )
        self.buildings_microgrid = BuildingsMicrogrid()
        self.critical_microgrid = CriticalMicrogrid()
        self.grid_to_in_house_links = self.init_grid_to_in_house_links()
        self.grid_to_out_house_links = self.init_grid_to_out_house_links()
        self.grid_to_apartment_links = self.init_grid_to_apartment_links()

        self.time = 0
        self.graph_periodicity = graph_periodicity

        self.town_battery = CentralUtilityBattery()

    def init_grid_to_in_house_links(self):
        return tuple(
            MicrogridToInMeter(microgrid, house)
            for microgrid in self.house_microgrids
            for house in microgrid.houses
        )

    def init_grid_to_out_house_links(self):
        return tuple(
            MicrogridToOutMeter(microgrid, house)
            for microgrid in self.house_microgrids
            for house in microgrid.houses
        )

    def init_grid_to_apartment_links(self):
        return tuple(
            MicrogridToApartmentMeter(self.buildings_microgrid, building, apartment)
            for building in self.buildings_microgrid.buildings
            for apartment in building.apartments
        )

    def get_house_in_meter_battery(self):
        for microgrid in self.house_microgrids:
            for house in microgrid.houses:
                yield house, house.smart_meter_in, house.battery

    def get_house_out_meter_battery(self):
        for microgrid in self.house_microgrids:
            for house in microgrid.houses:
                yield house, house.smart_meter_out, house.battery

    def get_microgrid_house(self):
        for microgrid in self.house_microgrids:
            for house in microgrid.houses:
                yield microgrid, house

    def get_houses(self):
        for microgrid in self.house_microgrids:
            for house in microgrid.houses:
                yield house

    pool = ProcessPoolExecutor(max_workers=4)

    def time_step(self):
        # time for all smart meters to collect data

        # f1 = self.pool.submit(self.record_power_stored)
        # f2 = self.pool.submit(self.record_power_through_in)
        # f3 = self.pool.submit(self.record_power_through_out)
        # f4 = self.pool.submit(self.update_power)
        #
        # for fut in concurrent.futures.as_completed([f1, f2, f3, f4]):
        #     fut.result()

        self.record_power_stored()
        self.record_power_through_in()
        self.record_power_through_out()
        self.update_power()

    def plot_power_use(self):
        data = np.array([house.power_consumed for house in self.get_houses()])
        print(
            f"min power consumption       {data.min():>20}\n"
            f"max power consumption       {data.max():>20}\n"
            f"std_dev                     {data.std():>20}\n"
            f"total power consumption     {sum(data):>20}"
        )
        plt.plot(np.arange(NUM_HOUSES), data)
        plt.savefig(f"{self.time}")

    @staticmethod
    def higher_than_average_use(time):
        return AVERAGE_PER_SECOND_USE * np.random.uniform(1.5, 3)

    @staticmethod
    def lower_than_average_use(time):
        return AVERAGE_PER_SECOND_USE * np.random.uniform(0.8, 1)

    def init(self):
        houses = list(self.get_houses())
        for idx, house in enumerate(houses):
            if idx % 10 == 0:
                house.set_power_consumption_function(self.higher_than_average_use)
            else:
                house.set_power_consumption_function(self.lower_than_average_use)
            house.battery.set_level(
                np.random.uniform(house.battery.minimum, house.battery.minimum + 0.25)
            )

    def handle_microgrid_controller(self):
        for microgrid in self.house_microgrids:
            for house in microgrid.houses:
                pass

    def run(self):
        self.init()
        all(
            house.battery.level_normalized() >= house.battery.minimum
            for house in self.get_houses()
        )
        while self.time < 24 * 60 * 60:
            if self.time % 200 == 0:
                print(self.time)
                self.plot_power_use()
            self.time_step()
            self.time += INTERVAL
            if self.time % 30 == 0:
                self.handle_microgrid_controller()

    def record_power_stored(self):
        for house, smart_meter_in, battery in self.get_house_in_meter_battery():
            smart_meter_in.record_history_log(
                RecordType.POWER_STORED,
                smart_meter_in.id,
                self.time,
                battery.level,
            )

    def record_power_through_in(self):
        for house, smart_meter_in, battery in self.get_house_in_meter_battery():
            smart_meter_in.record_history_log(
                RecordType.POWER_THROUGH,
                smart_meter_in.id,
                self.time,
                smart_meter_in.power_through,
            )

    def record_power_through_out(self):
        for house, smart_meter_out, battery in self.get_house_out_meter_battery():
            smart_meter_out.record_history_log(
                RecordType.POWER_THROUGH,
                smart_meter_out.id,
                self.time,
                smart_meter_out.power_through,
            )

    def update_power(self):
        for microgrid, house in self.get_microgrid_house():
            power_needed = house.consume_power(self.time, INTERVAL)  #
            if house.battery.level_normalized() <= house.battery.minimum:
                if microgrid.local_loop.has_extra_power():
                    microgrid.local_loop.consume(power_needed)
                    house.increment_power_consumed_by(power_needed)
                elif not self.town_battery.is_empty():
                    ratio_per_sec = power_needed / (
                        house.battery.per_second_use * INTERVAL
                    )
                    self.town_battery.deplete(ratio_per_sec)
                    # get power from town
                    house.smart_meter_in.power_through += power_needed
                    house.increment_power_consumed_by(power_needed)
                else:
                    print(f"{house} this house doesn't get power from anywhere")
            else:
                # level is above minimum
                house.increment_power_consumed_by(power_needed)
                ratio_per_sec = power_needed / (house.battery.per_second_use * INTERVAL)
                house.battery.deplete(ratio_per_sec)
            house.battery.charge(house.battery.per_second_use * 0.2)
            if house.battery.is_full():
                # should check that the rate that the battery is sending power is always >
                # rate of power generated
                house.smart_meter_out.power_through += house.battery.per_second_use


if __name__ == "__main__":
    controller = Controller()
    controller.run()
    controller.pool.shutdown()
    # gen_and_pickle_locations(plot=True)
    # clustered_locs = unpickle_clustered_locations()
    # plot_clusters(clustered_locs[:50])
