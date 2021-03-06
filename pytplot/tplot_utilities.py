# Copyright 2018 Regents of the University of Colorado. All Rights Reserved.
# Released under the MIT license.
# This software was developed at the University of Colorado's Laboratory for Atmospheric and Space Physics.
# Verify current version before use at: https://github.com/MAVENSDC/PyTplot

from __future__ import division
import os
import datetime
import pickle
import math
import pandas as pd
import numpy as np
import pytz
from _collections import OrderedDict
from . import data_quants
import pytplot

def compare_versions():
    #import libraries
    import requests

    #access complete list of revision numbers on PyPI 
    pytplot_url = "https://pypi.python.org/pypi/pytplot/json"
    try:
        pt_pypi_vn = sorted(requests.get(pytplot_url).json()['releases'])
    except:
        return
    
    #find PyPI version number
    pt_pypi_vn = pt_pypi_vn[-1]
    pr1 = pt_pypi_vn
    pt_pypi_vn = pt_pypi_vn.split(".")
    #convert to integer array for comparison
    pt_pypi_vn = [int(i) for i in pt_pypi_vn]
    
    #find current directory out of which code is executing
    dir_path = os.path.dirname(os.path.realpath(__file__))
    version_path = dir_path + '/version.txt'
    #open version.txt in current directory and read
    with open(version_path) as f:
        cur_vn = f.readline()
    cur_vn = "".join(cur_vn)
    pr2 = cur_vn
    cur_vn = cur_vn.split(".")
    #convert to integer array for comparison
    cur_vn = [int(i) for i in cur_vn]

    #for each item in version number array [X.Y.Z]
    for i in range(len(cur_vn)):
        #if current item > PyPI item (hypothetical), break, latest version is running
        if cur_vn[i] > pt_pypi_vn[i]:
            old_flag = 0
            break
        #if current item = PyPI item, continue to check next item
        elif cur_vn[i] == pt_pypi_vn[i]:
            old_flag = 0
            continue
        #if current item < PyPI item, indicative of old version, throw flag to initiate warning
        else:
            old_flag = 1
            break

    #if not running latest version, throw warning
    if old_flag == 1:
        print("PyPI PyTplot Version")
        print(pr1)
        print("Your PyTplot Version in " + dir_path)
        print(pr2)
        print("")
        print('****************************** WARNING! ******************************')
        print('*                                                                    *')
        print('*          You are running an outdated version of PyTplot.           *')
        print('*              Sync your module for the latest updates.              *')
        print('*                                                                    *')
        print('****************************** WARNING! ******************************')
    return 
        
def option_usage():
    print("options 'tplot variable name' 'plot option' value[s]")
    return

def set_tplot_options(option, value, old_tplot_opt_glob):
    new_tplot_opt_glob = old_tplot_opt_glob
    
    if option == 'title':
        new_tplot_opt_glob['title_text'] = value
    
    elif option == 'title_size':
        str_size = str(value) + 'pt'
        new_tplot_opt_glob['title_size'] = str_size
        
    elif option == 'wsize':
        new_tplot_opt_glob['window_size'] = value
        
    elif option == 'title_align':
        new_tplot_opt_glob['title_align'] = value
        
    elif option == 'var_label':
        new_tplot_opt_glob['var_label'] = value
        
    elif option == 'alt_range':
        new_tplot_opt_glob['alt_range'] = value
    
    return (new_tplot_opt_glob)

def str_to_int(time_str):
    epoch_t = "1970-1-1 00:00:00"
    pattern = "%Y-%m-%d %H:%M:%S"
    epoch_t1 = datetime.datetime.strptime(epoch_t, pattern)
    time_str1 = datetime.datetime.strptime(time_str, pattern)
    time_int = int((time_str1-epoch_t1).total_seconds())
    return time_int

def int_to_str(time_int):
    if math.isnan(time_int):
        return "NaN"
    else:
        return datetime.datetime.fromtimestamp(int(round(time_int)), tz=pytz.UTC).strftime("%Y-%m-%d %H:%M:%S")

def return_bokeh_colormap(name):
    import matplotlib as mpl
    #mpl.use('tkagg')
    from matplotlib import cm
    
    if name=='yellow':
        map = [rgb_to_hex(tuple((np.array([1,1,0,1])*255).astype(np.int))) for x in range(0,256)]
        return map
    elif name=='red':
        map = [rgb_to_hex(tuple((np.array([1,0,0,1])*255).astype(np.int))) for x in range(0,256)]
        return map
    elif name=='blue':
        map = [rgb_to_hex(tuple((np.array([0,0,1,1])*255).astype(np.int))) for x in range(0,256)]
        return map
    elif name=='green':
        map = [rgb_to_hex(tuple((np.array([0,1,0,1])*255).astype(np.int))) for x in range(0,256)]
        return map
    elif name=='purple':
        map = [rgb_to_hex(tuple((np.array([1,0,1,1])*255).astype(np.int))) for x in range(0,256)]
        return map
    elif name=='teal':
        map = [rgb_to_hex(tuple((np.array([0,1,1,1])*255).astype(np.int))) for x in range(0,256)]
        return map
    else:
        cm = mpl.cm.get_cmap(name)
        map = [rgb_to_hex(tuple((np.array(cm(x))*255).astype(np.int))) for x in range(0,cm.N)]
        return map

def rgb_to_hex(rgb):
    red = rgb[0]
    green = rgb[1]
    blue = rgb[2]
    return '#%02x%02x%02x' % (red, green, blue)

def get_heatmap_color(color_map, min_val, max_val, values, zscale = 'log'):
    colors = []
    if not isinstance(values, list):
        values = [values]
    for value in values:
        if np.isfinite(value):
            if value > max_val:
                value = max_val
            if value < min_val:
                colors.append("#%02x%02x%02x" % (255, 255, 255))
                continue
            if zscale=='log':
                log_min=np.log10(min_val)
                log_max=np.log10(max_val)
                log_val=np.log10(value)
                if np.isfinite(np.log10(value)):
                    cm_index = int((((log_val-log_min) / (log_max-log_min)) * (len(color_map)-1)))
                    colors.append(color_map[cm_index])
                else:
                    colors.append(("#%02x%02x%02x" % (255, 255, 255)))
            else:
                cm_index = int((((value-min_val) / (max_val-min_val)) * (len(color_map)-1)))
                colors.append(color_map[cm_index])
        else:
            colors.append("#%02x%02x%02x" % (255, 255, 255))
    return colors
    
def timebar_delete(t, varname=None, dim='height'):
    if varname is None:
        for name in pytplot.data_quants:
            list_timebars = pytplot.data_quants[name].time_bar
            elem_to_delete = []
            for elem in list_timebars:
                for num in t:
                    if (elem.location == num) and (elem.dimension == dim):
                        elem_to_delete.append(elem)
            for i in elem_to_delete:
                list_timebars.remove(i)
            pytplot.data_quants[name].time_bar = list_timebars
    else:
        if not isinstance(varname, list):
            varname = [varname]
        for i in varname:
            if i not in pytplot.data_quants.keys():
                print(str(i) + " is currently not in pytplot.")
                return
            list_timebars = pytplot.data_quants[i].time_bar
            elem_to_delete = []
            for elem in list_timebars:
                for num in t:
                    if (elem.location == num) and (elem.dimension == dim):
                        elem_to_delete.append(elem)
            for j in elem_to_delete:
                list_timebars.remove(j)
            pytplot.data_quants[i].time_bar = list_timebars
    return    

def return_lut(name):
    import matplotlib as mpl
    mpl.use('tkagg')
    from matplotlib import cm
    
    if name=='yellow':
        map = [(np.array([1,1,0,1])*255).astype(np.int) for x in range(0,256)]
        return map
    elif name=='red':
        map = [(np.array([1,0,0,1])*255).astype(np.int) for x in range(0,256)]
        return map
    elif name=='blue':
        map = [(np.array([0,0,1,1])*255).astype(np.int) for x in range(0,256)]
        return map
    elif name=='green':
        map = [(np.array([0,1,0,1])*255).astype(np.int) for x in range(0,256)]
        return map
    elif name=='purple':
        map = [(np.array([1,0,1,1])*255).astype(np.int) for x in range(0,256)]
        return map
    elif name=='teal':
        map = [(np.array([0,1,1,1])*255).astype(np.int) for x in range(0,256)]
        return map
    else:
        cm = mpl.cm.get_cmap(name)
        map = [(np.array(cm(x))*255).astype(np.int) for x in range(0,cm.N)]
        return map
    
def get_available_qt_window():
    #Delete old windows
    for w in pytplot.pytplotWindows:
        if not w.isVisible():
            del w
            
    #Add a new one to the list
    pytplot.pytplotWindows.append(pytplot.PlotWindow())
    
    #Return the latest window
    return pytplot.pytplotWindows[-1]

def rgb_color(color):
    color_opt = {
                'indianred':(205,92,92),
                'lightcoral':(240,128,128),
                'salmon':(250,128,114),
                'darksalmon':(233,150,122),
                'lightsalmon':(255,160,122),
                'crimson':(220,20,60),
                'red':(255,0,0),
                'firebrick':(178,34,34),
                'darkred':(139,0,0),
                
                'pink':(255,192,203),
                'lightpink':(255,182,193),
                'hotpink':(255,105,180),
                'deeppink':(255,20,147),
                'mediumvioletred':(199,21,133),
                'palevioletred':(219,112,147),
                
                'tomato':(255,99,71),
                'orangered':(255,69,0),
                'darkorange':(255,140,0),
                'orange':(255,165,0),
                
                'gold':(155,215,0),
                'yellow':(255,255,0),
                'lightyellow':(255,255,224),
                'lemonchiffon':(255,250,205),
                'lightgoldenrodyellow':(250,250,210),
                'papayawhip':(255,239,213),
                'moccasin':(255,228,181),
                'peachpuff':(255,218,185),
                'palegoldenrod':(238,232,170),
                'khaki':(240,230,130),
                'darkkhaki':(189,183,107),
                
                'lavender':(230,230,250),
                'thistle':(216,191,216),
                'plum':(221,160,221),
                'violet':(238,130,238),
                'orchid':(218,112,214),
                'fuchsia':(255,0,255),
                'magenta':(255,0,255),
                'mediumorchid':(186,85,211),
                'mediumpurple':(147,112,219),
                'rebeccapurple':(102,51,153),
                'blueviolet':(138,43,226),
                'darkviolet':(148,0,211),
                'darkorchid':(153,50,204),
                'darkmagenta':(139,0,139),
                'purple':(128,0,128),
                'indigo':(75,0,130),
                'slateblue':(106,90,205),
                'darkslateblue':(72,61,139),
                'mediumslateblue':(123,104,238),
                
                'greenyellow':(173,255,47),
                'chartreuse':(127,255,0),
                'lawngreen':(124,252,0),
                'lime':(0,255,0),
                'limegreen':(50,205,50),
                'palegreen':(152,251,152),
                'lightgreen':(144,238,144),
                'mediumspringgreen':(0,250,154),
                'springgreen':(0,255,127),
                'mediumseagreen':(60,179,113),
                'seagreen':(46,139,87),
                'forestgreen':(34,139,34),
                'green':(0,128,0),
                'darkgreen':(0,100,0),
                'yellowgreen':(154,205,50),
                'olivedrab':(107,142,35),
                'olive':(128,128,0),
                'darkolivegreen':(85,107,47),
                'mediumaquamarine':(102,205,170),
                'darkseagreen':(143,188,139),
                'lightseagreen':(32,178,170),
                'darkcyan':(0,139,139),
                'teal':(0,128,128),
                
                'aqua':(0,255,255),
                'cyan':(0,255,255),
                'lightcyan':(224,255,255),
                'paleturquoise':(175,238,238),
                'aquamarine':(127,255,212),
                'turquoise':(64,224,208),
                'mediumturquoise':(72,209,204),
                'darkturquoise':(0,206,209),
                'cadetblue':(95,158,160),
                'steelblue':(70,130,180),
                'lightsteelblue':(176,196,222),
                'powderblue':(176,224,230),
                'lightblue':(173,216,23),
                'skyblue':(135,206,235),
                'lightskyblue':(135,206,250),
                'deepskyblue':(0,191,255),
                'dodgerblue':(30,144,255),
                'cornflowerblue':(100,149,237),
                'royalblue':(65,105,225),
                'blue':(0,0,255),
                'mediumblue':(0,0,205),
                'darkblue':(0,0,139),
                'navy':(0,0,128),
                'midnightblue':(25,25,112),
                
                'cornsilk':(255,248,220),
                'blanchedalmond':(255,235,205),
                'bisque':(255,228,196),
                'navajowhite':(155,222,173),
                'wheat':(245,222,179),
                'burlywood':(222,184,135),
                'tan':(210,208,214),
                'rosybrown':(188,143,143),
                'sandybrown':(244,164,96),
                'goldenrod':(218,165,32),
                'darkgoldenrod':(184,134,11),
                'peru':(205,133,63),
                'chocolate':(210,105,30),
                'saddlebrown':(139,69,19),
                'sienna':(160,82,45),
                'brown':(165,42,42),
                'maroon':(128,0,0),
                'white':(255,255,255),
                'snow':(255,250,250),
                'honeydew':(240,255,240),
                'mintcream':(245,255,250),
                'azure':(240,255,255),
                'aliceblue':(240,248,255),
                'ghostwhite':(248,248,255),
                'whitesmoke':(245,245,245),
                'seashell':(255,245,238),
                'beige':(245,245,220),
                'oldlace':(253,245,230),
                'floralwhite':(255,250,240),
                'ivory':(255,255,240),
                'antiquewhite':(250,235,215),
                'linen':(250,240,230),
                'lavenderblush':(255,240,245),
                'mistyrose':(255,228,255),
                
                'gainsboro':(220,220,220),
                'lightgray':(211,211,211),
                'silver':(192,192,192),
                'darkgray':(169,169,169),
                'gray':(128,128,128),
                'dimgray':(105,105,105),
                'lightslategray':(119,136,153),
                'slategray':(112,128,144),
                'darkslategray':(47,79,79),
                'black':(0,0,0),
                
                'r':(255,0,0),
                'g':(0,128,0),
                'b':(0,0,255),
                'c':(0,255,255),
                'y':(255,255,0),
                'm':(255,0,255),
                'w':(255,255,255),
                'k':(0,0,0)
                 }

    if type(color) is not list:
        rgbcolor = color_opt[color]
    else:
        rgbcolor = len(color)*[0]
        for i,val in enumerate(color):
            rgbcolor[i] = color_opt[val]
    return rgbcolor
