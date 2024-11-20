import datetime
import os
import time

import requests


class PriceVolume:
    def __init__(self, price: float, volume: float):
        self.price = price
        self.volume = volume

    def __str__(self):
        return f"{self.price} {self.volume}"


class MimerData:
    def __init__(self, date: datetime.date):
        self.min_hours = 22  # 2024-03-31 and some other dates missing 1-2 hours
        self.date = date
        self.fcrn: list[PriceVolume] = []
        self.fcrd_up: list[PriceVolume] = []
        self.fcrd_down: list[PriceVolume] = []
        self.affr_up: list[PriceVolume] = []
        self.affr_down: list[PriceVolume] = []
        self.mffr_up: list[PriceVolume] = []
        self.mffr_down: list[PriceVolume] = []

    def validate_fcr(self):
        assert len(self.fcrn) >= self.min_hours, self.__str__()
        assert len(self.fcrd_up) >= self.min_hours, self.__str__()
        assert len(self.fcrd_down) >= self.min_hours, self.__str__()

    def validate_affr(self):
        assert len(self.affr_up) >= self.min_hours, self.__str__()
        assert len(self.affr_down) >= self.min_hours, self.__str__()

    def validate_mffr(self):
        assert len(self.mffr_up) >= self.min_hours, self.__str__()
        assert len(self.mffr_down) >= self.min_hours, self.__str__()

    def calculate_averages(self) -> list[int]:
        averages = [0, 0, 0, 0, 0, 0, 0]
        self.validate_fcr()
        self.validate_affr()
        self.validate_mffr()

        for price_volume in self.fcrn:
            averages[0] += price_volume.price
        averages[0] = round(averages[0] / len(self.fcrn))

        for price_volume in self.fcrd_up:
            averages[1] += price_volume.price
        averages[1] = round(averages[1] / len(self.fcrd_up))

        for price_volume in self.fcrd_down:
            averages[2] += price_volume.price
        averages[2] = round(averages[2] / len(self.fcrd_down))

        for price_volume in self.affr_up:
            averages[3] += price_volume.price
        averages[3] = round(averages[3] / len(self.affr_up))

        for price_volume in self.affr_down:
            averages[4] += price_volume.price
        averages[4] = round(averages[4] / len(self.affr_down))

        for price_volume in self.mffr_up:
            averages[5] += price_volume.price
        averages[5] = round(averages[5] / len(self.mffr_up))

        for price_volume in self.mffr_down:
            averages[6] += price_volume.price
        averages[6] = round(averages[6] / len(self.mffr_down))

        return averages

    def __str__(self):
        return f"{self.date} num hours fcr={len(self.fcrn)} fcrd_up={len(self.fcrd_up)} fcrd_down={len(self.fcrd_down)} affr_up={len(self.affr_up)} affr_down={len(self.affr_down)} mffr_up={len(self.mffr_up)} mffr_down={len(self.mffr_down)}"


def get_fcr_csv(from_param: str, to_param: str) -> list[str]:
    print(f"Downloading FCR")
    url = f"https://mimer.svk.se/PrimaryRegulation/DownloadText?{from_param}&{to_param}&auctionTypeId=1"
    #print(f"FCR URL: {url}")
    response = requests.get(url)
    return response.text.split("\n")[1:-2]


def get_affr_csv(from_param: str, to_param: str) -> list[str]:
    print(f"Downloading aFFR")
    url = f"https://mimer.svk.se/AutomaticFrequencyRestorationReserve/DownloadText?{from_param}&{to_param}"
    #print(f"aFFR URL: {url}")
    response = requests.get(url)
    return response.text.split("\n")[1:-2]


def get_mffr_csv(from_param: str, to_param: str) -> list[str]:
    print(f"Downloading mFFR")
    url = f"https://mimer.svk.se/ManualFrequencyRestorationReserve/DownloadText?{from_param}&{to_param}&ConstraintAreaId=0"
    #print(f"mFFR URL: {url}")
    response = requests.get(url)
    return response.text.split("\n")[1:-2]


def assert_equals(expected, actual, message):
    assert expected == actual, message


def two_digits(number: int) -> str:
    return f"{number:02d}"


def decimal2(number: str) -> float:
    return float(f"{float(number.replace(",", ".")):.2f}")


def handle_dates(from_date: datetime.date, to_date: datetime.date):
    data: dict = {}
    date = from_date
    while date <= to_date:
        data[date] = MimerData(date)
        date += datetime.timedelta(days=1)

    from_param = f"periodFrom={two_digits(from_date.month)}%2F{two_digits(from_date.day)}%2F{two_digits(from_date.year)}%2000%3A00%3A00"
    to_param = f"periodTo={two_digits(to_date.month)}%2F{two_digits(to_date.day)}%2F{two_digits(to_date.year)}%2000%3A00%3A00"
    print(f"Downloading {from_date} to {to_date}")

    num_hours_seen = 0
    for line in get_mffr_csv(from_param, to_param):
        columns = line.split(";")
        if columns[1] == "SN4":
            date = datetime.datetime.strptime(columns[0], "%Y-%m-%d %H:%M").date()
            data[date].mffr_up.append(PriceVolume(decimal2(columns[2]), decimal2(columns[3])))
            data[date].mffr_down.append(PriceVolume(decimal2(columns[4]), decimal2(columns[5])))
            num_hours_seen += 1

    time.sleep(3)
    num_hours_seen = 0
    for line in get_affr_csv(from_param, to_param):
        columns = line.split(";")
        if columns[1] == "SN4":
            date = datetime.datetime.strptime(columns[0], "%Y-%m-%d %H:%M").date()
            data[date].affr_up.append(PriceVolume(decimal2(columns[2]), decimal2(columns[3])))
            data[date].affr_down.append(PriceVolume(decimal2(columns[4]), decimal2(columns[5])))
            num_hours_seen += 1

    time.sleep(3)
    num_hours_seen = 0
    for line in get_fcr_csv(from_param, to_param):
        columns = line.split(";")
        date = datetime.datetime.strptime(columns[0], "%Y-%m-%d %H:%M:%S").date()
        data[date].fcrn.append(PriceVolume(decimal2(columns[1]), 0))
        data[date].fcrd_up.append(PriceVolume(decimal2(columns[8]), 0))
        data[date].fcrd_down.append(PriceVolume(decimal2(columns[15]), 0))
        num_hours_seen += 1

    filename = f"dist/data/{from_date.year}.csv"
    with open(filename, "a") as fd:
        date = from_date
        while date <= to_date:
            averages = data[date].calculate_averages()
            csv_line = f"{date},{",".join([str(x) for x in averages])}"
            print(f"Writing {csv_line}")
            fd.write(f"{csv_line}\n")
            date += datetime.timedelta(days=1)
    print(f"Wrote to {filename}")


def run():
    starting_year = 2023
    # TODO: aFFR was 2 days delayed on a Sunday. See if we can start earlier on weekdays
    end_date = datetime.date.today() - datetime.timedelta(days=2)

    for year in range(starting_year, end_date.year + 1, 1):
        year_end = datetime.date(year, 12, 31)
        if os.path.isfile(f"{year}.csv"):
            with open(f"{year}.csv", "r") as fd:
                for line in fd:
                    if not line.rstrip():
                        break
                last_date = datetime.datetime.strptime(line.split(",")[0], "%Y-%m-%d").date()
                if last_date >= end_date or last_date.month == 12 and last_date.day == 31:
                    print(f"Have all of {year}")
                    continue
                if year < end_date.year:
                    end_date = year_end
                if last_date < year_end:
                    handle_dates(last_date + datetime.timedelta(days=1), end_date)
        else:
            if year != end_date.year:
                handle_dates(datetime.date(year, 1, 1), year_end)
                time.sleep(10)
            else:
                handle_dates(datetime.date(year, 1, 1), end_date)


run()
print("Done")