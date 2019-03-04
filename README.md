# JARCH-Vis

## Introduction
JARCH Vis is add-on for Blender 3D that helps create certain
architectural objects in a way that makes them easily customizable.

The architecture types that can be created are:

* Siding
* Flooring
* Windows
* Roofing

## Usage
The JARCH Vis (JV) panel is found in the 3D Viewport Toolbar, under a
section called "JARCH Vis." There is always at least four buttons within
that panel, allowing an object of each architecture type to be easily
added to the scene. If a JV object is selected, then the options
specific to the architecture type of the selected object will be
displayed in the panel.

Modifying any value within the panel will automatically update the mesh
object, assuming that the `Update Automatically?` option is selected. If
that option is unchecked, then the `Update Object` button has to be
clicked to get the object to update. If the mesh object is really large
or complicated, then it might be a good idea to not update automatically.

#### Converting Objects
There are times when you might want to add objects that aren't
rectangular. This can be done by converting an object made up of planes
into a JV object. To convert an object, start by entering editmode.
Then, select all faces that are in the same plane/group and click the `+`
button in the JV panel. Repeat for all groups of faces.

##### Face Group
> In JARCH Vis, a face group is a collection of faces that all lie in
the same plane and will be used as a mask/boolean object for a JV object.
Essentially, a face group is used as a cookie-cutter. It is important
that all points lie in the same plane within a face group to ensure
expected results.

JV has two ways to use the face groups as cutter objects. One way is with
the boolean modifier, which supports non-convex face groups. However,
the boolean modifier sometimes returns odd results. If the face group
is convex, then check the `Convex?` option, which will cause JV to use a
different method of cutting the face group.

##### Convex
> A shape or polygon is convex if there does not exist a line segment
between two points on the surface that passes outside of the surface.
More specifically, a face group is convex if all interior angles between
boundary edges are less than or equal to 180 degrees and there are no
parts missing from the interior of the shape.

Once all face groups have been added, exit editmode and make sure that
the rotation and scale have been applied for the object: `CTRL+A ->
Rotation & Scale`. After that, just click `Convert Object` within the JV
panel. The newly converted JV object will have most of the same options
as a regular JV object, except the overall dimension values.

##### Cutouts
Cutouts provide an easy way to cut rectangles out of siding, roofing, and
flooring objects. Cutouts can even be added to objects that have been
converted. To add a cutout, first check the `Cutouts?` box, then click
`Add Cutout`. Every cutout has the following options:

* `Location` - the X, Y, and Z position of the corner of the cutout
* `Dimensions` - the X, Y, and Z dimensions of the cutout
* `Rotation` - the X, Y, and Z rotation of the cutout
* `Local` - whether or not the location and rotation of the cutout are in
local coordinates or not

A cutout can be removed by clicking the `Remove Cutout` button right below
the `Local` option.

> The `Local` option for a cutout can dramatically change where the
cutout is located. If `Local` is checked, then the `Location` and `Rotation`
values are offsets from object's origin and rotation. If `Local` is not
checked, then the values are in reference to the world and are absolute
positions.

#### Materials
The faces within JV objects are created in such a way that materials
can be added easily. By default, all faces will use the material in the
first slot on the object. However, glass and mortar faces will use the
second slot. Therefore adding materials is as easy as putting the primary
material in the first slot, and a secondary material, if needed, in the
second slot.

#### UV Unwrapping
All JV objects have UV seams added and are unwrapped automatically.

## Installation
1. Download the latest release or `.zip` version of the
repository.
2. Extract the downloaded folder and rename the it to `jarch_vis`.
Make sure that the file structure is like `jarch_vis/__init__.py` and not
`jarch_vis/some_folder/__init__.py`.
3. Move the `jarch_vis` folder to your Blender install location under
`2.8x/scripts/addons`. On Windows, this is generally found at
`Program Files/Blender Foundation/Blender/2.8x/...`
4. Open Blender, go to `Edit -> Preferences -> Add-ons` and check the
option that is `Add Mesh: JARCH Vis`.

## Revision Log
### JV 2.0.0 for Blender 2.8x
Version 2.0.0 represents a massive change in JARCH Vis. The entire add-on was re-written from the ground up. Changing the user-interface,
simplifying the backing code, allowing new architecture types to be
added more easily, and updating JV to work with Blender 2.8x.
It is important to note that backwards compatibility has been broken.
JV objects created with previous versions of JV will
not work with this newest version.

Changes in no particular order include:

* Stairs have been removed for the time being
* Two new patterns of flooring: Corridor and Octagons
* Hexagons and Octagons can have dots/cubes added between the tiles
* Several flooring patterns were renamed
* A new way of handling cutouts was added that is faster and allows for an
"unlimited" number of cutouts
* Most architecture pattern types are more customizable and many
arbitrary min and max bounds on values have been removed
* Several types of siding have been combined
* Shiplap siding, shakes, and scallop shakes have been added
* Tongue & Groove and Stone siding have been removed. Stone will hopefully
be added back in at some point. Tongue & Groove is likely gone for awhile.
* Shakes for roofing have been added
* Terracotta tiles have been updated to a slightly different look
* Gliding, double-hung, and stationary windows have all been combined
into the "Regular" pattern, with new options added to allow all the old
looks to be created
* Arch and Ellipse windows are built differently to make them smoother
at a lower resolution

## Goals
1. Add a much more customizable and faster version of stone siding
then previously existed
1. Add stairs back in
1. Add railing