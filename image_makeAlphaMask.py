# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy

bl_info = {
    "name": "Make Alpha Masked Image",
    "category": "Image",
    "author": "lucasvinbr (lucasvinbr@gmail.com)",
    "version": "0.2",
    "location": "Image Editor > Tools > Misc > Make Alpha Masked Copy",
    "description": "Makes a copy of currently displayed Image using another one as its alpha channel",
}


from bpy.props import (                    
                       StringProperty,
                       PointerProperty,
                       EnumProperty)

from bpy.types import (Operator,
                       Panel,
                       Scene
                       )

def makeAlphaMaskedImage(baseImg, maskImg, newImgName = "", channelAsNewAlpha = "B"):
    D = bpy.data
    
    #make duplicates of base and mask images since we'll be scaling them
    baseImgCpy = baseImg.copy()
    maskImgCpy = maskImg.copy()
    
    if newImgName.count("") > 0:
        baseImgCpy.name = newImgName
    else:
        baseImgCpy.name = baseImg.name + "_masked"
    
    maxSize = [max(baseImgCpy.size[0], maskImgCpy.size[0]), max(baseImgCpy.size[1], maskImgCpy.size[1])]
    
    baseImgCpy.scale(maxSize[0], maxSize[1])
    maskImgCpy.scale(maxSize[0], maxSize[1])
    
    resultPixs = list(baseImgCpy.pixels)
    maskPix = list(maskImgCpy.pixels)
    
    #the decrement sets which channel of the mask image we'll be applying as alpha.
    #0 -> A, 1 -> B, 2 -> G ...
    channelPickedDecrement = 0
    if channelAsNewAlpha == "B":
        channelPickedDecrement = 1
    elif channelAsNewAlpha == "G":
        channelPickedDecrement = 2
    elif channelAsNewAlpha == "R":
        channelPickedDecrement = 3
    
    #expecting image pixel data to go R, G, B, A, R, G, B...
    #this means element 3 (fourth element) is the first A
    for i in range(3, len(resultPixs), 4):
        resultPixs[i] = maskPix[i - channelPickedDecrement]
    
    baseImgCpy.pixels = resultPixs
    
    
    #cleanup...
    D.images.remove(maskImgCpy)
    
    return baseImgCpy



class MakeAlphaMaskedCopyOp(Operator):
    bl_idname = "image.make_masked_operator"
    bl_label = "Create Masked Image"
    
    @classmethod
    def poll(cls, context):
        sima = context.space_data
        
        return (sima and sima.image)
    
    def execute(self, context):
        sima = context.space_data
        curScene = context.scene
        if curScene.alphaMaskImg is None:
            self.report({"ERROR_INVALID_INPUT"},"Alpha Mask Image not specified")
        elif curScene.alphaMaskSourceImgChannel is None:
            self.report({"ERROR_INVALID_INPUT"},"Alpha Mask Channel not specified")
        else:
            makeAlphaMaskedImage(sima.image, curScene.alphaMaskImg, curScene.alphaMaskImgResultName, curScene.alphaMaskSourceImgChannel)
        
        
        return {'FINISHED'}


class MakeAlphaMaskedCopyPanel(Panel):
    """Panel in the Image Tools Tab"""
    bl_space_type = 'IMAGE_EDITOR'
    bl_region_type = 'TOOLS'
    bl_label = "Make Alpha Masked Copy"
    
    
    @classmethod
    def poll(cls, context):
        sima = context.space_data

        return (sima and sima.image)

    def draw(self, context):
        layout = self.layout
        sima = context.space_data
        curScene = context.scene
        
        row = layout.row().split(0.33)
        row.label(text="Alpha Mask:")
        row.template_ID(curScene, "alphaMaskImg", open="image.open")
        
        layout.separator()
        
        row = layout.row()
        row.prop(curScene, "alphaMaskImgResultName")
        
        row = layout.row()
        row.prop(curScene, "alphaMaskSourceImgChannel")
        
        row = layout.row()
        row.operator("image.make_masked_operator", "Create Masked Copy")

#--------------
#REGISTER\UNREGISTER
#--------------

classes = (
    MakeAlphaMaskedCopyPanel,
    MakeAlphaMaskedCopyOp
)

def register():
    from bpy.utils import register_class
    for cls in classes:
        register_class(cls)
        
    Scene.alphaMaskImg = PointerProperty(type=bpy.types.Image, name="Alpha Mask Image", description="File used as Alpha Mask in the Make Alpha Mask Addon")
    
    Scene.alphaMaskImgResultName = StringProperty(name="Resulting Image Name", description="Name of the image created as result of the masking. If empty, the resulting image will have the name of the base file with a suffix", maxlen=255)
    Scene.alphaMaskSourceImgChannel = EnumProperty(items=(("R", "R", "The Mask's Red channel will be used as alpha for the resulting image"),
        ("G", "G", "The Mask's Green channel will be used as alpha for the resulting image"),
        ("B", "B", "The Mask's Blue channel will be used as alpha for the resulting image"),
        ("A", "A", "The Mask's Alpha channel will be used as alpha for the resulting image")), 
    name="Channel Used for Masking", 
    description="Which of the color channels (R,G,B,A) will be used from the Mask Image?",
    default = "B")

def unregister():
    from bpy.utils import unregister_class
    for cls in reversed(classes):
        unregister_class(cls)
        
    del Scene.alphaMaskImg
    del Scene.alphaMaskImgResultName
    del Scene.alphaMaskSourceImgChannel

if __name__ == "__main__":
    register()
