# profile_generator.py
import random
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')

class ProfileGenerator:
    def __init__(self):
        self.custom_ranges = {}

    def assign_depths_to_zones(self, depth_values, zone_percentages):
        """Assigns depths to zones based on percentages."""
        zones = {}
        current_depth = 0
        for i, percentage in enumerate(zone_percentages):
            zone_end_index = int(len(depth_values) * (sum(zone_percentages[:i+1]) / 100))
            zone_end = depth_values[min(zone_end_index, len(depth_values) -1)]

            zones[i + 1] = (current_depth, zone_end)
            current_depth = zone_end
        return zones

    def generate_data(self, depth_values, zones):
        """Generates the data for the table."""
        data = []

        for d in depth_values:
            zone_num = None
            for z, (start, end) in zones.items():
                if start <= d <= end:
                    zone_num = z
                    break

            ranges = self.get_parameter_ranges(zone_num)

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
                    row[param] = self.generate_value(d, depth_values[-1], min_val, max_val, trend, param, zone_num, zones, data)
                else:
                    row[param] = 0

            if "OM" not in ranges:
                row["OM"], row["CC"], row["IM"] = 0, 0, 0
            else:
                row["OM"], row["CC"], row["IM"] = self.generate_sum_to_100(
                    ranges["OM"][0], ranges["OM"][1], ranges["OM"][2],
                    ranges["CC"][0], ranges["CC"][1], ranges["CC"][2],
                    ranges["IM"][0], ranges["IM"][1], ranges["IM"][2],
                    d, depth_values[-1]
                )
            if "Clay" not in ranges:
                row["Clay"], row["Silt"], row["Sand"] = 0, 0, 0
            else:
                row["Clay"], row["Silt"], row["Sand"] = self.generate_sum_to_100(
                    ranges["Clay"][0], ranges["Clay"][1], ranges["Clay"][2],
                    ranges["Silt"][0], ranges["Silt"][1], ranges["Silt"][2],
                    ranges["Sand"][0], ranges["Sand"][1], ranges["Sand"][2],
                    d, depth_values[-1]
                )
            data.append(row)
        return data


    def generate_value(self, d, depth, min_val, max_val, trend, param, zone_num, zones, data):
        """Generates a value based on the trend."""

        normalized_depth = d / depth if depth > 0 else 0

        if trend == "SP":
            if random.random() < 0.7:
                return round(0, 2)
            else:
                return round(random.uniform(min_val, max_val), 2)

        elif trend == "UP":
            if not hasattr(self, f'{param}_last_val_up'):
                setattr(self, f'{param}_last_val_up', min_val * 1.3)
            last_val_up = getattr(self, f'{param}_last_val_up')
            new_val = random.uniform(last_val_up, max_val * 0.7)
            setattr(self, f'{param}_last_val_up', new_val)
            return round(new_val, 2)

        elif trend == "DN":
            if not hasattr(self, f'{param}_last_val_dn'):
                setattr(self, f'{param}_last_val_dn', max_val * 0.7)
            last_val_dn = getattr(self, f'{param}_last_val_dn')
            new_val = random.uniform(min_val * 1.3, last_val_dn)
            setattr(self, f'{param}_last_val_dn', new_val)
            return round(new_val, 2)

        elif trend == "LF":
            if not hasattr(self, f'{param}_lf_center'):
                setattr(self, f'{param}_lf_center', (min_val + max_val) / 2)
            lf_center = getattr(self, f'{param}_lf_center')
            fluctuation = (max_val - min_val) * 0.4
            new_val = random.uniform(lf_center - fluctuation, lf_center + fluctuation)
            setattr(self, f'{param}_lf_center', new_val)
            return round(new_val, 2)

        elif trend == "HF":
            fluctuation = (max_val - min_val) * 0.8
            center = (min_val + max_val) / 2
            return round(random.uniform(center - fluctuation, center + fluctuation), 2)

        elif trend == "SL":
            midpoint_ratio = random.uniform(0.4, 0.6)
            midpoint = depth * midpoint_ratio
            if d <= midpoint:
                if not hasattr(self, f'{param}_stagnant_center_sl'):
                    setattr(self, f'{param}_stagnant_center_sl', random.uniform(min_val * 1.2, max_val * 0.8))
                stagnant_center_sl = getattr(self, f'{param}_stagnant_center_sl')
                fluctuation = (max_val - min_val) * 0.05
                return round(random.uniform(max(min_val, stagnant_center_sl - fluctuation), min(max_val, stagnant_center_sl + fluctuation)), 2)

            else:
                if not hasattr(self, f'{param}_last_val_sl'):
                    setattr(self, f'{param}_last_val_sl', getattr(self, f'{param}_stagnant_center_sl'))
                last_val_sl = getattr(self, f'{param}_last_val_sl')
                normalized_depth = (d - midpoint) / (depth - midpoint) if (depth - midpoint) > 0 else 0
                new_val = round(float(last_val_sl - (last_val_sl-min_val) * normalized_depth * 0.5 ),2)
                setattr(self, f'{param}_last_val_sl', new_val)
                return max(min_val, min(new_val, max_val))

        elif trend == "SH":
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
                    setattr(self, f'{param}_last_val_sh', getattr(self, f'{param}_stagnant_center_sh'))
                last_val_sh = getattr(self, f'{param}_last_val_sh')
                normalized_depth = (d - midpoint) / (depth - midpoint) if (depth - midpoint) > 0 else 0

                new_val = round(float(last_val_sh + (max_val - last_val_sh) * normalized_depth * 0.5),2)
                setattr(self, f'{param}_last_val_sh', new_val)
                return max(min_val, min(new_val, max_val))

        elif trend == "UD":
            midpoint_ratio = random.uniform(0.4, 0.6)
            midpoint = zones[zone_num][0] + (zones[zone_num][1] - zones[zone_num][0]) * midpoint_ratio

            if d <= midpoint:
                normalized_zone_depth = (d - zones[zone_num][0]) / (midpoint - zones[zone_num][0]) if (midpoint - zones[zone_num][0]) > 0 else 0
                return round(float(min_val + (max_val - min_val) * normalized_zone_depth), 2)
            else:
                normalized_zone_depth = (d - midpoint) / (zones[zone_num][1] - midpoint) if (zones[zone_num][1] - midpoint) > 0 else 0
                return round(float(max_val - (max_val - min_val) * normalized_zone_depth), 2)

        elif trend == "DU":
            midpoint_ratio = random.uniform(0.4, 0.6)
            midpoint = zones[zone_num][0] + (zones[zone_num][1] - zones[zone_num][0]) * midpoint_ratio

            if d <= midpoint:
                normalized_zone_depth = (d - zones[zone_num][0]) / (midpoint - zones[zone_num][0]) if (midpoint - zones[zone_num][0]) > 0 else 0
                return round(float(max_val - (max_val - min_val) * normalized_zone_depth), 2)
            else:
                normalized_zone_depth = (d - midpoint) / (zones[zone_num][1] - midpoint) if (zones[zone_num][1] - midpoint) > 0 else 0
                return round(float(min_val + (max_val - min_val) * normalized_zone_depth), 2)

        elif trend == "RM":
            return round(random.uniform(min_val, max_val), 2)


    def generate_profile(self, depth_choice, zone_percentages):
        """Generates the paleo profile based on user selections."""

        zones = self.assign_depths_to_zones(depth_choice, zone_percentages)
        data = self.generate_data(depth_choice, zones)
        return data

    def generate_sum_to_100(self, min1, max1, trend1, min2, max2, trend2, min3, max3, trend3, d, depth):
        """Generates three values that sum to 100."""
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


    def get_parameter_ranges(self, zone_num):
        """Gets parameter ranges, considering custom overrides."""

        if zone_num in self.custom_ranges:
            return self.custom_ranges[zone_num]

        ranges = {}

        # Generic ranges for all zones (no base_type or env_type)
        if zone_num == 5:
            ranges = {
                "OM": (0, 10, "LF"),
                "IM": (70, 95, "LF"),
                "CC": (12, 30, "LF"),
                "Clay": (0, 5, "LF"),
                "Silt": (5, 15, "HF"),
                "Sand": (70, 90, "HF"),
                "MS": (130, 220, "HF"),
                "CH": (0, 2, "SP"),
                "AP": (0, 10, "LF"),
                "NAP": (0, 10, "LF"),
                "WL": (0, 5, "LF"),
                "CR": (0, 5, "LF"),
                "Ca": (270, 400, "HF"),
                "Mg": (250, 330, "HF"),
                "Na": (300, 400, "HF"),
                "K": (300, 400, "HF")
            }

        elif zone_num == 4:
            ranges.update({
                "OM": (5, 25, "LF"),
                "IM": (40, 80, "LF"),
                "CC": (5, 35, "LF"),
                "Clay": (10, 20, "LF"),
                "Silt": (10, 60, "LF"),
                "Sand": (20, 40, "LF"),
                "MS": (100, 150, "LF"),
                "CH": (0, 4, "SP"),
                "AP": (100, 160, "LF"),
                "NAP": (20, 40, "HF"),
                "WL": (20, 50, "HF"),
                "CR": (115, 250, "LF"),
                "Ca": (150, 190, "HF"),
                "Mg": (110, 140, "HF"),
                "Na": (220, 310, "HF"),
                "K": (210, 330, "LF")
            })
        elif zone_num == 3:
            ranges.update({
                "OM": (9, 28, "LF"),
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

        elif zone_num == 2:
            ranges.update({
                "OM": (10, 35, "LF"),
                "IM": (40, 80, "HF"),
                "CC": (5, 40, "HF"),
                "Clay": (5, 40, "HF"),
                "Silt": (5, 60, "HF"),
                "Sand": (5, 60, "LF"),
                "MS": (50, 80, "LF"),
                "CH": (0, 3, "SP"),
                "AP": (45, 199, "LF"),
                "NAP": (40, 80, "HF"),
                "WL": (220, 340, "HF"),
                "CR": (0, 10, "SP"),
                "Ca": (630, 1200, "LF"),
                "Mg": (190, 230, "LF"),
                "Na": (200, 300, "LF"),
                "K": (200, 300, "LF")
            })

        elif zone_num == 1:
            ranges.update({
                "OM": (5, 25, "RM"),
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
            axes = [axes]

        for ax, col in zip(axes, df.columns):
            ax.step(df[col], df.index, where='post')
            ax.set_title(col, fontsize=9, rotation=0, ha='center')
            ax.invert_yaxis()
            ax.tick_params(axis='both', which='major', labelsize=6)
            ax.tick_params(axis='both', which='minor', labelsize=4)
            ax.set_ylim(df.index.max(), 0)

        fig.subplots_adjust(wspace=0.1)
        return fig
