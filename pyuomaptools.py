from PIL import Image
import struct

def load_gamefile_data(fpath):
    """Loads a binary game file at path 'fpath' into a buffer
    
    Returns the byte buffer
    """
    with open(fpath, 'rb') as f:
        buf = f.read()
    print "Loaded {:.3f} KBytes of game data from '{:s}'.".format(len(buf)/1024.0,fpath)
    return buf
    
def radar_color2rgb(rcode):
    """
    Converts "radar color codes"  to RGB values
    
    Ultima pixel colors are a 16-bit RGB555 value:
    
        15 | 14 | 13 | 12 | 11 | 10 | 9 | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0
        U  | R  | R  | R  | R  | R  | G | G | G | G | G | B | B | B | B | B
    
    The radar_color_buffer global holds the color lookup table from
    'radar color codes' to 16-bit RGB555 values.   
    
    (TODO: wrap all this in a class)
    
    Returns a tuple with (R,G,B)
    """
    offset   = 2*rcode # Byte offset into color lookup
    colorval = struct.unpack_from("H", radar_color_buffer, )
    return ( (( (colorval[0]>>10) & 0x1F ) << 3 ), # 8-bit R
             (( (colorval[0]>>5 ) & 0x1F ) << 3 ), # 8-bit G
             (( (colorval[0]>>0 ) & 0x1F ) << 3 )) # 8-bit B
   
def get_block(blkcoord):
    """
    Gets a block (8x8 pixels) worth of map data starting at the
    block coordinates (top-left) defined by tuple blkcoord.
    
    Block pixels are packed top-to-bottom, then left-to-right.
    
    Compute the byte offset into the map buffer and return the 
    block's bytes.
    
    """
    offset = block_size*(blkcoord[0]*mapblockv+blkcoord[1])
    return map_buffer[offset:offset+block_size]

def render_block(buffer):
    """
    Renders a block of byte data into pixels and returns both
    the map image (blkim) and the height map (zim, grayscale).
    
    Block data has a 4 byte header, followed by 64 24-bit words.
    
    Each 24-bit word is a 16-bit Radar Color Code and an 
    8-bit (signed) Z-height.    
    
    The pixel order follows "raster scan order", which is 
    left-to-right, then top-to-bottom.    
    """
    zim   = Image.new("RGB", (blockh,blockv), "black")
    zpix  = zim.load()
    blkim = Image.new("RGB", (blockh,blockv), "blue")
    bpix  = blkim.load()
    for v in range(0,blockv):
        for h in range(0,blockh):
            # Start at the header offset and unpack each 3-byte word
            (trccode,zval) = struct.unpack_from("Hb", buffer, 4+3*(8*v+h))
            bpix[h,v]    = radar_color2rgb(trccode)
            zpix[h,v]    = (128+zval,128+zval,128+zval)
    return (blkim,zim)

def render_map_area(start,size):
    """
    Renders an area of blocks starting at tuple 'start' (H,V)
    and continuing to tuple 'size' (H,V).
    
    Returns the rendered block image and Z-map.    
    """
    blkim = Image.new("RGB", (viewsizeh*blockh,viewsizev*blockv) , "black")
    zim   = Image.new("RGB", (viewsizeh*blockh,viewsizev*blockv) , "black")
    print "Rendering {:d}x{:d} block area, starting at ({:d},{:d})".format(size[0],size[1],start[0],start[1])
    for rblockv in range(start[1],start[1]+size[1]):
        for rblockh in range(start[0],start[0]+size[0]):
            (b  ,  z) = render_block(get_block((rblockh,rblockv)))
            (imh,imv) = (blockh*(rblockh-start[0]),blockv*(rblockv-start[1]))
            blkim.paste(b,(imh,imv))
            zim.paste(z,(imh,imv))
    return (blkim,zim)

# If invoked, run a quick test
if __name__ == "__main__":
    radar_color_buffer    = load_gamefile_data('radarcol.mul')
    map_buffer            = load_gamefile_data('map0.mul')
    
    block_size            = 196
    (blockh,blockv)       = (8,8)
    (mapblockh,mapblockv) = (896,512)
    (viewstrth,viewstrtv) = (0,0)
    (viewsizeh,viewsizev) = (896,512)
    
    (blkim,zim) = render_map_area((viewstrth,viewstrtv), (viewsizeh,viewsizev))
    blkim.save("map.png")
    zim.save("zmap.png")