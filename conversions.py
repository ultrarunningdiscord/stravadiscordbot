import math

class SpeedConversion():
    """Contains modules and helpers for converting meters per second to min/km or min/mile
    """
    def __init__(self):
        pass

    def convert(self, valueInMeters, unit="metric"):
        # conditionally converts from metric to imperial
        if unit == "imperial":
            return valueInMeters * 0.621371
        else:
            return valueInMeters

    def format(self, valueInMPS, unit="metric"):
        # converts and formats a meters/sec value into running pace
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
        """Converts m/s to running pace

        Args:
            mps (float): speed in meters per second
            showUnit (bool, optional): whether to also show unit. Defaults to True.

        Returns:
            str: speed in min/km
        """
        unit = " min/km"
        unitStr = unit if showUnit else ""
        return f"{self.format(mps, unit='metric')}{unitStr}"

    def getMinPerMile(self, mps, showUnit=True):
        """Converts m/s to running pace

        Args:
            mps (float): speed in meters per second
            showUnit (bool, optional): whether to also show unit. Defaults to True.

        Returns:
            str: speed in min/mile
        """
        unit = " min/mile"
        unitStr = unit if showUnit else ""
        return f"{self.format(mps, unit='imperial')}{unitStr}"

class DistanceConversion():
    """Contains modules and helpers for converting meters to km or miles
    """
    def __init__(self):
        pass

    def convert(self, valueInMeters, granularity="km", unit="metric"):
        val = valueInMeters if granularity == "m" else valueInMeters / 1000
        if unit == "imperial":
            return val * 3.28084 if granularity == "m" else val * 0.621371
        else:
            return val
            
    def round(self, value, roundTo=2, granularity="km"):
        converted = self.convert(value, granularity, unit="imperial")
        return "{:,}".format(round(converted, roundTo))

    def metersToMiles(self, meters, showUnit=True, roundTo=2):
        """Converts meters to miles

        Args:
            meters (float): distance in meters
            showUnit (bool, optional): whether to also show unit. Defaults to True.

        Returns:
            str: distance in miles
        """
        unit = " miles"
        unitStr = unit if showUnit else ""
        return self.round(meters, roundTo=roundTo) + unitStr

    def metersToFeet(self, meters, showUnit=True, roundTo=2):
        feet = meters * 3.28084
        unit = " ft"
        unitStr = unit if showUnit else ""
        return "{:,}".format(round(feet, roundTo)) + unitStr

# create instances of classes
distConversion = DistanceConversion()
speedConversion = SpeedConversion()

# export functions as standalone for minimal boilerplate
metersToMiles = distConversion.metersToMiles
metersToFeet = distConversion.metersToFeet
getMinPerKm = speedConversion.getMinPerKm
getMinPerMile = speedConversion.getMinPerMile