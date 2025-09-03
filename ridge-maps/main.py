# %pip install ridge_map

# http://bboxfinder.com/#0.000000,0.000000,0.000000,0.000000

from ridge_map import RidgeMap
import matplotlib.pyplot as plt

rm = RidgeMap((  -122.199576,42.891522,-121.992865,42.993366 ))

values = rm.get_elevation_data(num_lines=50)

rm.plot_map(values=rm.preprocess(values=values, water_ntile=12, vertical_ratio=50),
            label='crater\n   lake',
            label_x=0.75,
            label_y=0.82,
            linewidth=3,
            line_color='green')

plt.savefig('output/crater-lake-green.png', bbox_inches='tight', pad_inches=0, dpi=300)
