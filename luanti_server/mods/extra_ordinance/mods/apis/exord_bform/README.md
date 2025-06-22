
# WORK IN PROGRESS
Most elements are not implemented.

The below may or may not be up to date.

## Formspec implementation progress
- object based elements (first time in 10 years I've seen a legitimate use for OOP)
- flow; most elements allow nesting and use their size to determine the extend of their parent, so that things flow similar to HTML elements
- automatic second factor authentication with hidden fields and sha1 (doesn't stop mitm, only targets impersonation / spoofing)
- changing any part of a formspec will trigger callbacks (only if setter functions used)
- automatically, based on the above, don't recalculate formspecs unless changes have happened, or it's forced
- on_fields callbacks work
- can add elements to any named / id'd element
- even if you don't add an ID to something like a button, its callbacks will still work
- can inject other methods into a "custom" formspec object, which can do anything you want manually
- you can easily just add more element classes too instead
- negative numbers for `dir` are not allowed - flowing elements in reverse is too much work

## Elements Implemented
- formspec (with size, version etc)
- field, button, image_button
- image
- list
- style_type
- container, scroll_container



# To do

## High priority

- `scrollbar[<X>,<Y>;<W>,<H>;<orientation>;<name>;<value>]`
- `scrollbaroptions[opt1;opt2;...]`
- `item_image_button[<X>,<Y>;<W>,<H>;<item name>;<name>;<label>]`
- `style[<selector 1>,<selector 2>,...;<prop1>;<prop2>;...]`
- `set_focus[<name>;<force>]`
- `bgcolor[<bgcolor>;<fullscreen>;<fbgcolor>]`
- `background[<X>,<Y>;<W>,<H>;<texture name>;<auto_clip>]`
- `background9[<X>,<Y>;<W>,<H>;<texture name>;<auto_clip>;<middle>]`
- `box[<X>,<Y>;<W>,<H>;<color>]`
- `label[<X>,<Y>;<label>]`
- `vertlabel[<X>,<Y>;<label>]`

## Low priority

- `pwdfield[<X>,<Y>;<W>,<H>;<name>;<label>]`
- `textarea[<X>,<Y>;<W>,<H>;<name>;<label>;<default>]`
- `table[<X>,<Y>;<W>,<H>;<name>;<cell 1>,<cell 2>,...,<cell n>;<selected idx>]`
- `textlist[<X>,<Y>;<W>,<H>;<name>;<listelem 1>,<listelem 2>,...,<listelem n>;<selected idx>;<transparent>]` --> use child nodes, add class for `listelem`
- `tabheader[<X>,<Y>;<W>,<H>;<name>;<caption 1>,<caption 2>,...,<caption n>;<current_tab>;<transparent>;<draw_border>]`
- `dropdown[<X>,<Y>;<W>,<H>;<name>;<item 1>,<item 2>, ...,<item n>;<selected idx>;<index event>]`
- `checkbox[<X>,<Y>;<name>;<label>;<selected>]`
- `hypertext[<X>,<Y>;<W>,<H>;<name>;<text>]`
- `tooltip[<gui_element_name>;<tooltip_text>;<bgcolor>;<fontcolor>]` --> use id of parent if not given
- `tooltip[<X>,<Y>;<W>,<H>;<tooltip_text>;<bgcolor>;<fontcolor>]` --> use size of parent if no size given
- `model[<X>,<Y>;<W>,<H>;<name>;<mesh>;<textures>;<rotation X,Y>;<continuous>;<mouse control>;<frame loop range>;<animation speed>]`
- `item_image[<X>,<Y>;<W>,<H>;<item name>]`
- `tableoptions[<opt 1>;<opt 2>;...]`
- `tablecolumns[<type 1>,<opt 1a>,<opt 1b>,...;<type 2>,<opt 2a>,<opt 2b>;...]`