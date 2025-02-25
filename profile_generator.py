# profile_generator.py
import random
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')  # Use Agg backend to save plots

class ProfileGenerator:
    def __init__(self):
        self.custom_ranges = {}  # Store custom ranges
        #self.zones = [1, 2, 3, 4, 5] #Removed, using dynamic zones now

    def assign_depths_to_zones(self, depth_values, zone_percentages):
        """Assigns depths to zones based on percentages."""
        zones = {}
        current_depth = 0
        for i, percentage in enumerate(zone_percentages):
            zone_end_index = int(len(depth_values) * (sum(zone_percentages[:i+1]) / 100))  # Calculate index
            zone_end = depth_values[min(zone_end_index, len(depth_values) -1)] #Get value for the index, prevent error

            zones[i + 1] = (current_depth, zone_end)
            current_depth = zone_end
        return zones

    def generate_data(self, depth_values, zones, base_type, env_type):
        """Generates the data for the table."""
        data = []

        for d in depth_values:
            zone_num = None
            for z, (start, end) in zones.items():
                if start <= d <= end:
                    zone_num = z
                    break

            ranges = self.get_parameter_ranges(base_type, env_type, zone_num)

            row = {
                "Depth": d,
                "Zone": zone_num,
                "OM": 0, "CC": 0, "IM": 0,
                "Clay": 0, "Silt": 0, "Sand": 0,
            }

            all_params = ["MS", "CH", "AP", "NAP", "WL", "CR", "Ca", "Mg", "Na", "K"]
            for param in all_params:
                if param in ranges:
                    min_val, max_val, trend = ranges[param]
                    row[param] = self.generate_value(d, depth_values[-1], min_val, max_val, trend, param, zone_num, zones, data)  # depth_values[-1] is max_depth
                else:
                    row[param] = 0

            if "OM" not in ranges:
                row["OM"], row["CC"], row["IM"] = 0, 0, 0
            else:
                row["OM"], row["CC"], row["IM"] = self.generate_sum_to_100(
                    ranges["OM"][0], ranges["OM"][1], ranges["OM"][2],
                    ranges["CC"][0], ranges["CC"][1], ranges["CC"][2],
                    ranges["IM"][0], ranges["IM"][1], ranges["IM"][2],
                    d, depth_values[-1] #max_depth
                )
            if "Clay" not in ranges:
                row["Clay"], row["Silt"], row["Sand"] = 0, 0, 0
            else:
                row["Clay"], row["Silt"], row["Sand"] = self.generate_sum_to_100(
                    ranges["Clay"][0], ranges["Clay"][1], ranges["Clay"][2],
                    ranges["Silt"][0], ranges["Silt"][1], ranges["Silt"][2],
                    ranges["Sand"][0], ranges["Sand"][1], ranges["Sand"][2],
                    d, depth_values[-1] #max_depth
                )
            data.append(row)
        return data


    def generate_value(self, d, depth, min_val, max_val, trend, param, zone_num, zones, data):
        """Generates a value based on the trend."""

        normalized_depth = d / depth if depth > 0 else 0

        if trend == "SP":  # Sporadic: 70% chance to be 0
            if random.random() < 0.7:
                return round(0, 2)
            else:
                return round(random.uniform(min_val, max_val), 2)

        elif trend == "UP":  # Up: Increasing values
            if not hasattr(self, f'{param}_last_val_up'):
                setattr(self, f'{param}_last_val_up', min_val * 1.3)  # Initialize
            last_val_up = getattr(self, f'{param}_last_val_up')
            new_val = random.uniform(last_val_up, max_val * 0.7)
            setattr(self, f'{param}_last_val_up', new_val)
            return round(new_val, 2)

        elif trend == "DN":  # Down: Decreasing values
            if not hasattr(self, f'{param}_last_val_dn'):
                setattr(self, f'{param}_last_val_dn', max_val * 0.7) # Initialize
            last_val_dn = getattr(self, f'{param}_last_val_dn')
            new_val = random.uniform(min_val * 1.3, last_val_dn)
            setattr(self, f'{param}_last_val_dn', new_val)
            return round(new_val, 2)

        elif trend == "LF":  # LowFluctuation
            if not hasattr(self, f'{param}_lf_center'):
                setattr(self, f'{param}_lf_center', (min_val + max_val) / 2)   # or some other initial value
            lf_center = getattr(self, f'{param}_lf_center')
            fluctuation = (max_val - min_val) * 0.4  # 40% fluctuation
            new_val = random.uniform(lf_center - fluctuation, lf_center + fluctuation)
            setattr(self, f'{param}_lf_center', new_val)  # Update center for next call, creating slow drift
            return round(new_val, 2)

        elif trend == "HF":  # HighFluctuation
            fluctuation = (max_val - min_val) * 0.8  # 80% fluctuation
            center = (min_val + max_val) / 2
            return round(random.uniform(center - fluctuation, center + fluctuation), 2)

        elif trend == "SL": #StagnantLow: first stagnant, then decreasing
            midpoint_ratio = random.uniform(0.4, 0.6)
            midpoint = depth * midpoint_ratio
            if d <= midpoint:
                if not hasattr(self, f'{param}_stagnant_center_sl'):
                    setattr(self, f'{param}_stagnant_center_sl', random.uniform(min_val * 1.2, max_val * 0.8))
                stagnant_center_sl = getattr(self, f'{param}_stagnant_center_sl')
                fluctuation = (max_val - min_val) * 0.05  # 5% fluctuation
                return round(random.uniform(max(min_val, stagnant_center_sl - fluctuation), min(max_val, stagnant_center_sl + fluctuation)), 2)

            else:
                if not hasattr(self, f'{param}_last_val_sl'):
                    setattr(self, f'{param}_last_val_sl', getattr(self, f'{param}_stagnant_center_sl'))#initialize with the stagnant value
                last_val_sl = getattr(self, f'{param}_last_val_sl')
                normalized_depth = (d - midpoint) / (depth - midpoint) if (depth - midpoint) > 0 else 0
                new_val = round(float(last_val_sl - (last_val_sl-min_val) * normalized_depth * 0.5 ),2) #slower decreasing
                setattr(self, f'{param}_last_val_sl', new_val)
                return max(min_val, min(new_val, max_val)) #Limit the value

        elif trend == "SH": #StagnantHigh: first stagnant, then increasing
            midpoint_ratio = random.uniform(0.4, 0.6)
            midpoint = depth * midpoint_ratio
            if d <= midpoint:
                if not hasattr(self, f'{param}_stagnant_center_sh'):
                    setattr(self, f'{param}_stagnant_center_sh', random.uniform(min_val * 1.2, max_val * 0.8))
                stagnant_center_sh = getattr(self, f'{param}_stagnant_center_sh')
                fluctuation = (max_val - min_val) * 0.05
                return round(random.uniform(max(min_val, stagnant_center_sh - fluctuation), min(max_val, stagnant_center_sh + fluctuation)), 2)
            else:
                if not hasattr(self, f'{param}_last_val_sh'):
                    setattr(self, f'{param}_last_val_sh', getattr(self, f'{param}_stagnant_center_sh')) #initialize with the stagnant value
                last_val_sh = getattr(self, f'{param}_last_val_sh')
                normalized_depth = (d - midpoint) / (depth - midpoint) if (depth - midpoint) > 0 else 0

                new_val = round(float(last_val_sh + (max_val - last_val_sh) * normalized_depth * 0.5),2) #Slower increasing
                setattr(self, f'{param}_last_val_sh', new_val)
                return max(min_val, min(new_val, max_val))  #Limit the value

        elif trend == "UD":  # UpDown
            midpoint_ratio = random.uniform(0.4, 0.6)
            midpoint = zones[zone_num][0] + (zones[zone_num][1] - zones[zone_num][0]) * midpoint_ratio

            if d <= midpoint:
                # Increasing part
                normalized_zone_depth = (d - zones[zone_num][0]) / (midpoint - zones[zone_num][0]) if (midpoint - zones[zone_num][0]) > 0 else 0
                return round(float(min_val + (max_val - min_val) * normalized_zone_depth), 2)
            else:
                # Decreasing part
                normalized_zone_depth = (d - midpoint) / (zones[zone_num][1] - midpoint) if (zones[zone_num][1] - midpoint) > 0 else 0
                return round(float(max_val - (max_val - min_val) * normalized_zone_depth), 2)

        elif trend == "DU":  # DownUp
            midpoint_ratio = random.uniform(0.4, 0.6)
            midpoint = zones[zone_num][0] + (zones[zone_num][1] - zones[zone_num][0]) * midpoint_ratio

            if d <= midpoint:
                # Decreasing part
                normalized_zone_depth = (d - zones[zone_num][0]) / (midpoint - zones[zone_num][0]) if (midpoint - zones[zone_num][0]) > 0 else 0
                return round(float(max_val - (max_val - min_val) * normalized_zone_depth), 2)
            else:
                # Increasing part
                normalized_zone_depth = (d - midpoint) / (zones[zone_num][1] - midpoint) if (zones[zone_num][1] - midpoint) > 0 else 0
                return round(float(min_val + (max_val - min_val) * normalized_zone_depth), 2)

        elif trend == "RM": # Random
            return round(random.uniform(min_val, max_val), 2)


    def generate_profile(self, depth_choice, base_type, env_type):
        """Generates the paleo profile based on user selections."""

        depth_ranges = {1: (50, 100), 2: (100, 200), 3: (200, 300), 4: (300, 400), 5: (400, 500), 6: (500, 600)}
        min_depth, max_depth = depth_ranges[depth_choice]
        depth = random.randrange(min_depth, max_depth + 1, 2)

        zone_percentages = self.generate_unique_zone_percentages()
        zones = self.assign_depths_to_zones(depth, zone_percentages)
        data = self.generate_data(depth, zones, base_type, env_type)
        return data

    def generate_sum_to_100(self, min1, max1, trend1, min2, max2, trend2, min3, max3, trend3, d, depth):
        """Generates three values that sum to 100, respecting bounds and trends."""
        max_attempts = 100
        for _ in range(max_attempts):
            v1 = self.generate_value(d, depth, min1, max1, trend1, "", 0, {}, [])
            v2 = self.generate_value(d, depth, min2, max2, trend2, "", 0, {}, [])
            v3 = self.generate_value(d, depth, min3, max3, trend3, "", 0, {}, [])

            if v1 + v2 + v3 == 0:
                return 0.00, 0.00, 0.00

            total = v1 + v2 + v3
            p1 = round((v1 / total) * 100, 2)
            p2 = round((v2 / total) * 100, 2)
            p3 = round(100 - p1 - p2, 2)

            if min1 <= p1 <= max1 and min2 <= p2 <= max2 and min3 <= p3 <= max3:
                return p1, p2, p3

        v1 = round(max(min1, min(max1, 33.33)), 2)
        v2 = round(max(min2, min(max2, 33.33)), 2)
        v3 = round(100 - v1 - v2, 2)

        if v3 < min3:
            deficit = min3 - v3
            if v1 > min1 + deficit / 2 and v2 > min2 + deficit / 2:
                v1, v2, v3 = round(v1 - deficit / 2, 2), round(v2 - deficit / 2, 2), round(min3, 2)
        elif v3 > max3:
            excess = v3 - max3
            v1, v2, v3 = round(v1 + excess / 2, 2), round(v2 + excess / 2, 2), round(max3, 2)

        return round(v1, 2), round(v2, 2), round(100 - v1 - v2, 2)


    def get_parameter_ranges(self, base_type, env_type, zone_num):
        """Gets parameter ranges, considering custom overrides."""

        # Check for custom ranges first
        if (zone_num, base_type, env_type) in self.custom_ranges:
            return self.custom_ranges[(zone_num, base_type, env_type)]

        ranges = {}  # Initialize ranges

        if zone_num == 5:  # Base type only applies to zone 5
            if base_type == "Rock":
                ranges = {
                    "OM": (0, 0, "LF"),
                    "IM": (70, 95, "LF"),
                    "CC": (12, 30, "LF"),
                    "Clay": (0, 5, "LF"),
                    "Silt": (5, 15, "HF"),
                    "Sand": (70, 90, "HF"),
                    "MS": (130, 220, "HF"),
                    "CH": (0, 0, "SP"),
                    "AP": (0, 0, "LF"),
                    "NAP": (0, 0, "LF"),
                    "WL": (0, 0, "LF"),
                    "CR": (0, 0, "LF"),
                    "Ca": (270, 400, "HF"),
                    "Mg": (250, 330, "HF"),
                    "Na": (300, 400, "HF"),
                    "K": (300, 400, "HF")
                }
            elif base_type == "Sand":
                ranges = {
                    "OM": (0, 0, "LF"),
                    "IM": (70, 95, "LF"),
                    "CC": (5, 20, "LF"),
                    "Clay": (0, 5, "UP"),
                    "Silt": (0, 10, "UP"),
                    "Sand": (85, 95, "UP"),
                    "MS": (150, 200, "LF"),
                    "CH": (0, 0, "SP"),
                    "AP": (20, 60, "LF"),
                    "NAP": (0, 20, "LF"),
                    "WL": (0, 0, "LF"),
                    "CR": (30, 90, "LF"),
                    "Ca": (70, 100, "LF"),
                    "Mg": (50, 90, "LF"),
                    "Na": (100, 150, "LF"),
                    "K": (100, 140, "LF")
                }
            elif base_type == "Paleosol":
                ranges = {
                    "OM": (0, 30, "LF"),
                    "IM": (30, 80, "LF"),
                    "CC": (0, 30, "LF"),
                    "Clay": (0, 30, "LF"),
                    "Silt": (0, 30, "LF"),
                    "Sand": (0, 90, "LF"),
                    "MS": (100, 150, "LF"),
                    "CH": (0, 10, "SP"),
                    "AP": (130, 280, "LF"),
                    "NAP": (10, 90, "LF"),
                    "WL": (40, 100, "LF"),
                    "CR": (60, 90, "LF"),
                    "Ca": (100, 200, "HF"),
                    "Mg": (100, 130, "HF"),
                    "Na": (100, 200, "LF"),
                    "K": (100, 200, "LF")
                }
            elif base_type == "Lake sediment":
                ranges = {
                    "OM": (5, 20, "LF"),
                    "IM": (40, 90, "LF"),
                    "CC": (5, 30, "LF"),
                    "Clay": (10, 20, "LF"),
                    "Silt": (10, 60, "LF"),
                    "Sand": (20, 40, "LF"),
                    "MS": (100, 150, "LF"),
                    "CH": (0, 10, "SP"),
                    "AP": (120, 260, "LF"),
                    "NAP": (20, 90, "LF"),
                    "WL": (10, 30, "UP"),
                    "CR": (130, 290, "LF"),
                    "Ca": (130, 200, "HF"),
                    "Mg": (90, 130, "HF"),
                    "Na": (200, 300, "LF"),
                    "K": (200, 300, "LF")
                }
        # Zones 1-4, influenced by env_type
        elif zone_num == 4:
            if env_type == "Lake":
                ranges.update({
                    "OM": (5, 20, "LF"),
                    "IM": (40, 80, "LF"),
                    "CC": (5, 35, "LF"),
                    "Clay": (10, 20, "LF"),
                    "Silt": (10, 60, "LF"),
                    "Sand": (20, 40, "LF"),
                    "MS": (100, 150, "LF"),
                    "CH": (0, 0, "SP"),
                    "AP": (100, 160, "LF"),
                    "NAP": (20, 40, "HF"),
                    "WL": (20, 50, "HF"),
                    "CR": (115, 250, "LF"),
                    "Ca": (150, 190, "HF"),
                    "Mg": (110, 140, "HF"),
                    "Na": (220, 310, "HF"),
                    "K": (210, 330, "LF")
                })
            elif env_type == "Peatland":
                ranges.update({
                    "OM": (30, 60, "UP"),
                    "IM": (40, 80, "UP"),
                    "CC": (5, 10, "UP"),
                    "Clay": (10, 20, "UP"),
                    "Silt": (10, 60, "UP"),
                    "Sand": (20, 40, "UP"),
                    "MS": (100, 150, "LF"),
                    "CH": (0, 8, "SP"),
                    "AP": (45, 199, "LF"),
                    "NAP": (40, 80, "HF"),
                    "WL": (40, 140, "HF"),
                    "CR": (30, 90, "LF"),
                    "Ca": (130, 200, "LF"),
                    "Mg": (90, 130, "LF"),
                    "Na": (200, 300, "LF"),
                    "K": (200, 300, "LF")
                })
            elif env_type == "Wetland":
                ranges.update({
                    "OM": (5, 30, "LF"),
                    "IM": (40, 90, "LF"),
                    "CC": (5, 30, "LF"),
                    "Clay": (10, 20, "LF"),
                    "Silt": (10, 60, "LF"),
                    "Sand": (20, 40, "LF"),
                    "MS": (100, 150, "LF"),
                    "CH": (0, 0, "SP"),
                    "AP": (45, 199, "LF"),
                    "NAP": (40, 80, "HF"),
                    "WL": (140, 240, "HF"),
                    "CR": (50, 120, "LF"),
                    "Ca": (130, 200, "HF"),
                    "Mg": (90, 130, "HF"),
                    "Na": (200, 300, "HF"),
                    "K": (200, 300, "HF")
                })

        elif zone_num == 3:
            if env_type == "Lake":
                ranges.update({
                    "OM": (9, 18, "LF"),
                    "IM": (40, 90, "LF"),
                    "CC": (5, 30, "LF"),
                    "Clay": (5, 40, "LF"),
                    "Silt": (5, 60, "LF"),
                    "Sand": (5, 60, "LF"),
                    "MS": (100, 150, "HF"),
                    "CH": (0, 5, "SP"),
                    "AP": (45, 199, "LF"),
                    "NAP": (40, 80, "HF"),
                    "WL": (40, 140, "HF"),
                    "CR": (30, 90, "LF"),
                    "Ca": (130, 200, "HF"),
                    "Mg": (90, 130, "LF"),
                    "Na": (200, 300, "HF"),
                    "K": (200, 300, "HF")
                })
            elif env_type == "Peatland":
              ranges.update({
                "OM": (30, 60, "UP"),
                "IM": (20, 60, "UP"),
                "CC": (5, 30, "UP"),
                "Clay": (5, 40, "UP"),
                "Silt": (5, 60, "UP"),
                "Sand": (5, 40, "UP"),
                "MS": (50, 100, "LF"),
                "CH": (0, 5, "SP"),
                "AP": (45, 199, "LF"),
                "NAP": (40, 80, "HF"),
                "WL": (220, 340, "HF"),
                "CR": (0, 30, "SP"),
                "Ca": (130, 200, "LF"),
                "Mg": (90, 130, "LF"),
                "Na": (200, 300, "LF"),
                "K": (200, 300, "LF")
            })
            elif env_type == "Wetland":
                ranges.update({
                    "OM": (10, 30, "LF"),
                    "IM": (30, 70, "LF"),
                    "CC": (20, 40, "LF"),
                    "Clay": (10, 40, "LF"),
                    "Silt": (20, 60, "LF"),
                    "Sand": (10, 50, "LF"),
                    "MS": (40, 70, "LF"),
                    "CH": (0, 5, "SP"),
                    "AP": (45, 199, "LF"),
                    "NAP": (40, 80, "HF"),
                    "WL": (220, 340, "HF"),
                    "CR": (0, 30, "SP"),
                    "Ca": (830, 1400, "LF"),
                    "Mg": (390, 530, "LF"),
                    "Na": (200, 300, "LF"),
                    "K": (200, 300, "LF")
                })

        elif zone_num == 2:
            if env_type == "Lake":
                ranges.update({
                    "OM": (10, 30, "LF"),
                    "IM": (40, 80, "HF"),
                    "CC": (5, 40, "HF"),
                    "Clay": (5, 40, "HF"),
                    "Silt": (5, 60, "HF"),
                    "Sand": (5, 60, "LF"),
                    "MS": (50, 80, "LF"),
                    "CH": (0, 0, "SP"),
                    "AP": (45, 199, "LF"),
                    "NAP": (40, 80, "HF"),
                    "WL": (220, 340, "HF"),
                    "CR": (0, 10, "SP"),
                    "Ca": (630, 1200, "LF"),
                    "Mg": (190, 230, "LF"),
                    "Na": (200, 300, "LF"),
                    "K": (200, 300, "LF")
                })
            elif env_type == "Peatland":
              ranges.update({
                "OM": (80, 99, "RM"),
                "IM": (1, 10, "HF"),
                "CC": (1, 5, "HF"),
                "Clay": (20, 60, "UP"),
                "Silt": (20, 60, "UP"),
                "Sand": (1, 5, "UP"),
                "MS": (20, 40, "LF"),
                "CH": (0, 0, "SP"),
                "AP": (45, 80, "LF"),
                "NAP": (140, 180, "HF"),
                "WL": (220, 340, "HF"),
                "CR": (0, 10, "SP"),
                "Ca": (630, 1200, "LF"),
                "Mg": (190, 230, "LF"),
                "Na": (500, 600, "LF"),
                "K": (500, 600, "LF")
            })
            elif env_type == "Wetland":
                ranges.update({
                    "OM": (50, 90, "LF"),
                    "IM": (5, 30, "HF"),
                    "CC": (5, 15, "HF"),
                    "Clay": (20, 60, "LF"),
                    "Silt": (20, 60, "LF"),
                    "Sand": (1, 5, "LF"),
                    "MS": (120, 140, "HF"),
                    "CH": (0, 10, "SP"),
                    "AP": (45, 80, "LF"),
                    "NAP": (140, 180, "HF"),
                    "WL": (220, 340, "HF"),
                    "CR": (0, 10, "SP"),
                    "Ca": (130, 200, "LF"),
                    "Mg": (90, 130, "LF"),
                    "Na": (500, 600, "LF"),
                    "K": (500, 600, "LF")
                })

        elif zone_num == 1:
            if env_type == "Lake":
                ranges.update({
                    "OM": (5, 15, "RM"),
                    "IM": (40, 80, "RM"),
                    "CC": (5, 30, "RM"),
                    "Clay": (5, 40, "LF"),
                    "Silt": (10, 60, "LF"),
                    "Sand": (20, 60, "LF"),
                    "MS": (150, 300, "HF"),
                    "CH": (0, 15, "SP"),
                    "AP": (145, 180, "LF"),
                    "NAP": (340, 480, "HF"),
                    "WL": (220, 340, "HF"),
                    "CR": (0, 30, "SP"),
                    "Ca": (190, 240, "LF"),
                    "Mg": (90, 130, "LF"),
                    "Na": (400, 600, "LF"),
                    "K": (400, 500, "LF")
                })
            elif env_type == "Peatland":
              ranges.update({
                "OM": (25, 70, "HF"),
                "IM": (40, 80, "RM"),
                "CC": (5, 20, "RM"),
                "Clay": (5, 40, "LF"),
                "Silt": (10, 60, "LF"),
                "Sand": (20, 60, "LF"),
                "MS": (150, 300, "HF"),
                "CH": (0, 15, "SP"),
                "AP": (145, 180, "LF"),
                "NAP": (340, 480, "HF"),
                "WL": (220, 340, "HF"),
                "CR": (0, 30, "SP"),
                "Ca": (190, 240, "LF"),
                "Mg": (90, 130, "LF"),
                "Na": (600, 900, "LF"),
                "K": (600, 900, "LF")
            })
            elif env_type == "Wetland":
                ranges.update({
                    "OM": (30, 70, "HF"),
                    "IM": (10, 80, "HF"),
                    "CC": (5, 30, "HF"),
                    "Clay": (5, 20, "LF"),
                    "Silt": (30, 60, "LF"),
                    "Sand": (40, 70, "LF"),
                    "MS": (400, 700, "LF"),
                    "CH": (0, 15, "SP"),
                    "AP": (145, 280, "LF"),
                    "NAP": (340, 480, "LF"),
                    "WL": (220, 340, "LF"),
                    "CR": (0, 30, "SP"),
                    "Ca": (130, 250, "LF"),
                    "Mg": (90, 230, "LF"),
                    "Na": (800, 900, "LF"),
                    "K": (800, 900, "LF")
                })

        return ranges

    def generate_diagram(self, data):
        """Generates the Matplotlib diagram."""
        if not data:
            return None

        df = pd.DataFrame(data)
        df = df.set_index('Depth')
        df = df.drop('Zone', axis=1)

        fig, axes = plt.subplots(nrows=1, ncols=len(df.columns), figsize=(10, 6), sharey=True)

        if len(df.columns) == 1:
            axes = [axes]  # Ensure axes is always a list

        for ax, col in zip(axes, df.columns):
            ax.step(df[col], df.index, where='post')
            ax.set_title(col, fontsize=9, rotation=0, ha='center')
            ax.invert_yaxis()
            ax.tick_params(axis='both', which='major', labelsize=6)
            ax.tick_params(axis='both', which='minor', labelsize=4)
            ax.set_ylim(df.index.max(), 0)

        fig.subplots_adjust(wspace=0.1)
        return fig  # Correctly return the figure object
