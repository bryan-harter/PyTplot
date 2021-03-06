import pyqtgraph as pg
import numpy as np
from pyqtgraph.Qt import QtCore
from pyqtgraph import functions as fn
from pyqtgraph.Point import Point
from pyqtgraph import debug as debug
import collections
from pytplot import tplot_opt_glob

class UpdatingImage(pg.ImageItem):
    
    _MAX_IMAGE_WIDTH = 10000
    _MAX_IMAGE_HEIGHT = 200
    
    def __init__(self, data, spec_bins, ascending_descending, ytype, ztype, lut, zmin, zmax):
        pg.ImageItem.__init__(self)
        
        if ztype=='log':
            data[data <= 0] = np.NaN
            self.data = np.log10(data)
            self.zmin = np.log10(zmin)
            self.zmax = np.log10(zmax)
        else:
            self.data = data
            self.zmin = zmin
            self.zmax = zmax
        self.lut = lut
        self.bin_sizes = spec_bins
        self.bins_inc = ascending_descending
        self.w = 100
        self.h = 100
        self.x = self.data.index.tolist()
        if ytype=='log':
            self.y = np.log10(self.bin_sizes.iloc[0])
        else:
            self.y = self.bin_sizes.iloc[0]
        self.picturenotgened=True
        self.generatePicture()
        

    def generatePicture(self, pixel_size=None):
        
        xmin = np.nanmin(self.x)
        xmax = np.nanmax(self.x)
        ymin = self.y.min().min()
        ymax= self.y.max().max()
        if pixel_size is None:
            width_in_pixels = tplot_opt_glob['window_size'][0]
            height_in_pixels = tplot_opt_glob['window_size'][1]
            width_in_plot_coords = tplot_opt_glob['window_size'][0]
            height_in_plot_coords = tplot_opt_glob['window_size'][1]
        else:
            width_in_pixels = pixel_size.width()
            height_in_pixels = pixel_size.height()
            width_in_plot_coords = self.getViewBox().viewRect().width()
            height_in_plot_coords = self.getViewBox().viewRect().height()
        
        image_width_in_plot_coords = int(xmax - xmin)
        image_height_in_plot_coords = int(ymax - ymin)
        
        image_width_in_pixels = int(image_width_in_plot_coords/width_in_plot_coords * width_in_pixels)
        image_height_in_pixels = int(image_height_in_plot_coords/height_in_plot_coords * height_in_pixels)
        if image_width_in_pixels > self._MAX_IMAGE_WIDTH:
            image_width_in_pixels = self._MAX_IMAGE_WIDTH
        if image_height_in_pixels > self._MAX_IMAGE_HEIGHT:
            image_height_in_pixels = self._MAX_IMAGE_HEIGHT
        if self.w != image_width_in_pixels or self.h != image_height_in_pixels:
            self.w = image_width_in_pixels
            self.h = image_height_in_pixels
            data = np.zeros((self.h,self.w))
            
            xp = np.linspace(xmin, xmax, self.w)
            yp = np.linspace(ymin, ymax, self.h)

            closest_xs = np.searchsorted(self.x, xp)
            y_sort = np.argsort(self.y.values)
            #if len(self.bin_sizes) == 1:
            closest_ys = np.searchsorted(self.y.values, yp, sorter=y_sort)
            if not self.bins_inc:
                closest_ys = np.flipud(closest_ys)
            data = self.data.iloc[closest_xs][closest_ys].values
            #else:
            #    for j in range(0,self.w):
            #        closest_ys = np.searchsorted(self.y.iloc[closest_xs[j]], yp, sorter=y_sort)
            #        data[:,j] = self.data.iloc[closest_xs[j]].iloc[closest_ys].values
            
            self.setImage(data.T, levels=(self.zmin, self.zmax))

            #Image can't handle NaNs, but you can set nan to the minimum and make the minimum transparent.  
            self.setLookupTable(self.lut, update=False)
            self.setRect(QtCore.QRectF(xmin,ymin,xmax-xmin,ymax-ymin))
            return
        
    def paint(self, p, *args):
        '''
        I have no idea why, but we need to generate the picture after painting otherwise 
        it draws incorrectly.  
        '''
        if self.picturenotgened:
            self.generatePicture(self.getBoundingParents()[0].rect())
            self.picturenotgened = False
        pg.ImageItem.paint(self, p, *args)
        self.generatePicture(self.getBoundingParents()[0].rect())
        
        
    def render(self):
        #The same as pyqtgraph's ImageItem.render, with the exception that the makeARGB function is slightly different
        
        profile = debug.Profiler()
        if self.image is None or self.image.size == 0:
            return
        if isinstance(self.lut, collections.Callable):
            lut = self.lut(self.image)
        else:
            lut = self.lut

        if self.autoDownsample:
            # reduce dimensions of image based on screen resolution
            o = self.mapToDevice(QtCore.QPointF(0,0))
            x = self.mapToDevice(QtCore.QPointF(1,0))
            y = self.mapToDevice(QtCore.QPointF(0,1))
            w = Point(x-o).length()
            h = Point(y-o).length()
            if w == 0 or h == 0:
                self.qimage = None
                return
            xds = max(1, int(1.0 / w))
            yds = max(1, int(1.0 / h))
            axes = [1, 0] if self.axisOrder == 'row-major' else [0, 1]
            image = fn.downsample(self.image, xds, axis=axes[0])
            image = fn.downsample(image, yds, axis=axes[1])
            self._lastDownsample = (xds, yds)
        else:
            image = self.image

        # if the image data is a small int, then we can combine levels + lut
        # into a single lut for better performance
        levels = self.levels
        if levels is not None and levels.ndim == 1 and image.dtype in (np.ubyte, np.uint16):
            if self._effectiveLut is None:
                eflsize = 2**(image.itemsize*8)
                ind = np.arange(eflsize)
                minlev, maxlev = levels
                levdiff = maxlev - minlev
                levdiff = 1 if levdiff == 0 else levdiff  # don't allow division by 0
                if lut is None:
                    efflut = fn.rescaleData(ind, scale=255./levdiff, 
                                            offset=minlev, dtype=np.ubyte)
                else:
                    lutdtype = np.min_scalar_type(lut.shape[0]-1)
                    efflut = fn.rescaleData(ind, scale=(lut.shape[0]-1)/levdiff,
                                            offset=minlev, dtype=lutdtype, clip=(0, lut.shape[0]-1))
                    efflut = lut[efflut]
                
                self._effectiveLut = efflut
            lut = self._effectiveLut
            levels = None
        
        # Assume images are in column-major order for backward compatibility
        # (most images are in row-major order)
        
        if self.axisOrder == 'col-major':
            image = image.transpose((1, 0, 2)[:image.ndim])
        
        argb, alpha = makeARGBwithNaNs(image, lut=lut, levels=levels)
        self.qimage = fn.makeQImage(argb, alpha, transpose=False)

    def setImage(self, image=None, autoLevels=None, **kargs):
        """
        Same this as ImageItem.setImage, but we don't update the drawing
        """
        
        profile = debug.Profiler()

        gotNewData = False
        if image is None:
            if self.image is None:
                return
        else:
            gotNewData = True
            shapeChanged = (self.image is None or image.shape != self.image.shape)
            image = image.view(np.ndarray)
            if self.image is None or image.dtype != self.image.dtype:
                self._effectiveLut = None
            self.image = image
            if self.image.shape[0] > 2**15-1 or self.image.shape[1] > 2**15-1:
                if 'autoDownsample' not in kargs:
                    kargs['autoDownsample'] = True
            if shapeChanged:
                self.prepareGeometryChange()
                self.informViewBoundsChanged()

        profile()

        if autoLevels is None:
            if 'levels' in kargs:
                autoLevels = False
            else:
                autoLevels = True
        if autoLevels:
            img = self.image
            while img.size > 2**16:
                img = img[::2, ::2]
            mn, mx = img.min(), img.max()
            if mn == mx:
                mn = 0
                mx = 255
            kargs['levels'] = [mn,mx]

        profile()

        self.setOpts(update=False, **kargs)

        profile()

        self.qimage = None
        self.update()

        profile()

        if gotNewData:
            self.sigImageChanged.emit()
            
    
def makeARGBwithNaNs(data, lut=None, levels=None, scale=None, useRGBA=False): 
    """ 
    This is the same as pyqtgraph.makeARGB, except that all NaN's in the data are set to transparent pixels
    """
    
    nanlocations = np.isnan(data)
    profile = debug.Profiler()

    if data.ndim not in (2, 3):
        raise TypeError("data must be 2D or 3D")
    if data.ndim == 3 and data.shape[2] > 4:
        raise TypeError("data.shape[2] must be <= 4")
    
    if lut is not None and not isinstance(lut, np.ndarray):
        lut = np.array(lut)
    
    if levels is None:
        # automatically decide levels based on data dtype
        if data.dtype.kind == 'u':
            levels = np.array([0, 2**(data.itemsize*8)-1])
        elif data.dtype.kind == 'i':
            s = 2**(data.itemsize*8 - 1)
            levels = np.array([-s, s-1])
        elif data.dtype.kind == 'b':
            levels = np.array([0,1])
        else:
            raise Exception('levels argument is required for float input types')
    if not isinstance(levels, np.ndarray):
        levels = np.array(levels)
    if levels.ndim == 1:
        if levels.shape[0] != 2:
            raise Exception('levels argument must have length 2')
    elif levels.ndim == 2:
        if lut is not None and lut.ndim > 1:
            raise Exception('Cannot make ARGB data when both levels and lut have ndim > 2')
        if levels.shape != (data.shape[-1], 2):
            raise Exception('levels must have shape (data.shape[-1], 2)')
    else:
        raise Exception("levels argument must be 1D or 2D (got shape=%s)." % repr(levels.shape))

    profile()

    # Decide on maximum scaled value
    if scale is None:
        if lut is not None:
            scale = lut.shape[0] - 1
        else:
            scale = 255.

    # Decide on the dtype we want after scaling
    if lut is None:
        dtype = np.ubyte
    else:
        dtype = np.min_scalar_type(lut.shape[0]-1)
            
    # Apply levels if given
    if levels is not None:
        if isinstance(levels, np.ndarray) and levels.ndim == 2:
            # we are going to rescale each channel independently
            if levels.shape[0] != data.shape[-1]:
                raise Exception("When rescaling multi-channel data, there must be the same number of levels as channels (data.shape[-1] == levels.shape[0])")
            newData = np.empty(data.shape, dtype=int)
            for i in range(data.shape[-1]):
                minVal, maxVal = levels[i]
                if minVal == maxVal:
                    maxVal += 1e-16
                newData[...,i] = fn.rescaleData(data[...,i], scale/(maxVal-minVal), minVal, dtype=dtype)
            data = newData
        else:
            # Apply level scaling unless it would have no effect on the data
            minVal, maxVal = levels
            if minVal != 0 or maxVal != scale:
                if minVal == maxVal:
                    maxVal += 1e-16
                data = fn.rescaleData(data, scale/(maxVal-minVal), minVal, dtype=dtype)
            

    profile()

    # apply LUT if given
    if lut is not None:
        data = fn.applyLookupTable(data, lut)
    else:
        if data.dtype is not np.ubyte:
            data = np.clip(data, 0, 255).astype(np.ubyte)
    
    #Set NaNs to transparent
    data[nanlocations] = [0,0,0,0]
    
    profile()

    # this will be the final image array
    imgData = np.empty(data.shape[:2]+(4,), dtype=np.ubyte)

    profile()

    # decide channel order
    if useRGBA:
        order = [0,1,2,3] # array comes out RGBA
    else:
        order = [2,1,0,3] # for some reason, the colors line up as BGR in the final image.
        
    # copy data into image array
    if data.ndim == 2:
        # This is tempting:
        #   imgData[..., :3] = data[..., np.newaxis]
        # ..but it turns out this is faster:
        for i in range(3):
            imgData[..., i] = data
    elif data.shape[2] == 1:
        for i in range(3):
            imgData[..., i] = data[..., 0]
    else:
        for i in range(0, data.shape[2]):
            imgData[..., i] = data[..., order[i]] 
        
    profile()
    
    # add opaque alpha channel if needed
    if data.ndim == 2 or data.shape[2] == 3:
        alpha = False
        imgData[..., 3] = 255
    else:
        alpha = True
        
    profile()
    return imgData, alpha