# drawing_primitives.py
from PIL import Image, ImageDraw
import math

def draw_origin_dot(img: Image.Image, origin: tuple, r: int = 10, color: str = "deepskyblue") -> Image.Image:
    """
    Draws a circular dot with a label for the origin on the given PIL Image.

    Args:
        img (PIL.Image.Image): The image to draw on.
        origin (tuple): (x, y) coordinates of the origin.
        r (int): Radius of the dot.
        color (str): Color of the dot (e.g., "deepskyblue", "#RRGGBB").

    Returns:
        PIL.Image.Image: The modified image.
    """
    d = ImageDraw.Draw(img)
    x, y = origin
    d.ellipse([x-r, y-r, x+r, y+r], fill=color, outline="navy", width=2)
    d.text((x+r+3, y-r-2), "Origin", fill=color)
    return img

def draw_arrow(d: ImageDraw.ImageDraw, start: tuple, end: tuple, fill: str = "orange", 
                width: int = 4, ah: int = 14, outline_color: str = "black", 
                outline_width_increase: int = 2):
    """
    Draws a line with an arrowhead at the end point, with an optional outline.

    Args:
        d (PIL.ImageDraw.ImageDraw): The ImageDraw object to use for drawing.
        start (tuple): (x, y) start coordinates of the arrow.
        end (tuple): (x, y) end coordinates of the arrow (where arrowhead is).
        fill (str): Fill color of the arrow (line and head).
        width (int): Line width of the arrow.
        ah (int): Arrowhead size (length from tip to base of triangle).
        outline_color (str): Color of the outline around the arrow.
        outline_width_increase (int): How much wider the outline should be than the main line.
    """
    # Draw outline first for a visual border effect
    if outline_width_increase > 0:
        d.line([start, end], fill=outline_color, width=width + outline_width_increase)
        # Calculate angle for arrowhead outline
        ang = math.atan2(end[1]-start[1], end[0]-start[0])
        p1_outline = end
        p2_outline = (end[0]-(ah+outline_width_increase)*math.cos(ang-math.pi/8), end[1]-(ah+outline_width_increase)*math.sin(ang-math.pi/8))
        p3_outline = (end[0]-(ah+outline_width_increase)*math.cos(ang+math.pi/8), end[1]-(ah+outline_width_increase)*math.sin(ang+math.pi/8))
        d.polygon([p1_outline,p2_outline,p3_outline], fill=outline_color)

    # Draw main arrow (line and arrowhead)
    d.line([start, end], fill=fill, width=width)
    # Calculate angle for main arrowhead
    ang = math.atan2(end[1]-start[1], end[0]-start[0])
    p1 = end
    p2 = (end[0]-ah*math.cos(ang-math.pi/8), end[1]-ah*math.sin(ang-math.pi/8))
    p3 = (end[0]-ah*math.cos(ang+math.pi/8), end[1]-ah*math.sin(ang+math.pi/8))
    d.polygon([p1,p2,p3], fill=fill)

def get_object_id(obj: dict) -> tuple | None:
    """
    Generates a unique ID for a drawable object from st_canvas's json_data.
    This helps in tracking newly drawn objects and preventing duplicate processing.

    Args:
        obj (dict): A dictionary representing a drawn object from st_canvas's json_data.

    Returns:
        tuple | None: A unique identifier tuple for the object, or None if type is not recognized.
    """
    obj_type = obj.get("type")
    if obj_type == "line":
        # Use all relevant coordinates and some properties for a unique ID for lines.
        # This makes the ID more robust against very similar, but distinct, lines.
        return (obj.get("x1"), obj.get("y1"), obj.get("x2"), obj.get("y2"),
                obj.get("strokeWidth"), obj.get("strokeColor"), obj_type)
    elif obj_type == "point":
        return (obj.get("x"), obj.get("y"), obj_type)
    elif obj_type == "circle":
        # For circles, use its bounding box and radius for a unique ID
        return (obj.get("left"), obj.get("top"), obj.get("radius"), obj_type)
    return None # Should not happen for valid drawable objects
