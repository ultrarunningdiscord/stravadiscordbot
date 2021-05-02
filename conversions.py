import math

class SpeedConversion():
    def __init__(self):
        pass

    def convert(self, valueInMeters, unit="metric"):
        if unit == "imperial":
            return valueInMeters * 0.621371
        else:
            return valueInMeters

    def format(self, valueInMPS, unit="metric"):
        converted = self.convert(valueInMPS, unit)
        minper = 16.666666667 / converted
        hours = math.floor(minper / 60)
        minutes = math.floor(minper - (hours * 3600) / 60)
        seconds = math.floor(minper * 60 - hours * 3600 - minutes * 60)

        if hours:
            return str(hours) + ":" + ("0" if minutes < 10 else "") + str(minutes) + ":" + ("0" if seconds < 10 else "") + str(seconds)
        else:
            return str(minutes) + ":" + ("0" if seconds < 10 else "") + str(seconds)

    def getMinPerKm(self, mps, showUnit=True):
        unit = " min/km"
        unitStr = unit if showUnit else ""

        return f"{self.format(mps, unit='metric')}{unitStr}"

    def getMinPerMile(self, mps, showUnit=True):
        unit = " min/mile"
        unitStr = unit if showUnit else ""

        return f"{self.format(mps, unit='imperial')}{unitStr}"

class DistanceConversion():
    def __init__(self):
        pass

    def convert(self, valueInMeters, granularity="km", unit="metric"):
        val = valueInMeters if granularity == "m" else valueInMeters / 1000
        if unit == "imperial":
            return val * 3.28084 if granularity == "m" else val * 0.621371
        else:
            return val
            
    def round(self, value, roundTo=1, granularity="km"):
        converted = self.convert(value, granularity, unit="imperial")
        sign = 1 if converted >= 0 else -1
        return "{:.{}f}".format((
            round(converted * math.pow(10, roundTo) + sign * 0.0001) /
            math.pow(10, roundTo)), roundTo
        )

    def meters2miles(self, meters, showUnit=True):
        unit = " miles"
        unitStr = unit if showUnit else ""

        return f"{self.round(meters)}{unitStr}"
