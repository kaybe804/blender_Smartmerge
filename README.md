# blender_Smartmerge

A plugin that allows merging vertices by distance, but keeping information about the original toplogy of the object intact. 
Found under 3d Viewport -> Sidebar -> SmartMerge.

Usage:
Select object -> Press Smart Merge -> make any changes that don't change the topology -> Press Smart Restore

WARNING: The smart merge is applied to the original object. If you want to keep the original object (e.g. to join the restored object as a shapekey), create a copy of it first and smart merge the copy instead.
