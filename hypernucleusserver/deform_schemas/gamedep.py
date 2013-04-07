from ..lib.gamedeplib import GameDepLib
from colander import (MappingSchema, SchemaNode, String, Decimal, OneOf, deferred, 
    Invalid, Regex)
from deform import FileData
from deform.widget import (TextAreaWidget, TextInputWidget, RadioChoiceWidget, 
    FileUploadWidget, SelectWidget)
import zipfile
#import Image

@deferred
def valid_picture(node, kw):
    """ checks to make sure uploaded file is a picture """
    def validator(node, value):
        try:
            """
            im = Image.open(value['fp'])
            im.getpixel((1,1))
            """
            pass
        except IOError:
            raise Invalid(node, 'The uploaded file is not a picture.')
    return validator

@deferred
def valid_source_file(node, kw):
    """ checks to make sure uploaded file is a valid zip """
    def validator(node, value):
        req_file_folder = kw.get("req_file_folder")
        try:
            z = zipfile.ZipFile(value['fp'])
            count = 0
            namelist = z.namelist()
            # Loop through files in required files and folders.
            for item in req_file_folder:
                # Make sure they are in the zip
                if item in namelist:
                    count += 1
            # If they are not all there, then...
            if not count == len(req_file_folder):
                # Make a list of files and folders for the Invalid exception
                filelist = ""
                for item in req_file_folder:
                    filelist += "%s, " % item
                filelist = filelist[:-2]
                raise Invalid(node,
                    'The zip must have the following files: %s' % filelist)
        except zipfile.BadZipfile:
            raise Invalid(node, 'The uploaded file is not a zip.')
    return validator

class ValidBinaryFile(object):

    def __init__(self, f):
        self.f = f

    def __call__(self, *args):
        if args[1]["gamedep_type"] == "dependencies":
            return valid_source_file(*args)
        else:
            return self.f(*args)

@deferred
@ValidBinaryFile
def valid_binary_file(node, kw):
    pass

class TmpStore(dict):
    """ Instances of this class implement the
    :class:`deform.interfaces.FileUploadTempStore` interface"""
    def preview_url(self, uid):
        return None

@deferred
def deferred_operating_system_widget(node, kw):
    g = GameDepLib(kw.get('gamedep_type'))
    return RadioChoiceWidget(values=g.list_operatingsystems())

@deferred
def deferred_operating_system_validator(node, kw):
    g = GameDepLib(kw.get('gamedep_type'))
    return OneOf(g.list_operatingsystems(False))

@deferred
def deferred_architecture_widget(node, kw):
    g = GameDepLib(kw.get('gamedep_type'))
    return RadioChoiceWidget(values=g.list_architectures())

@deferred
def deferred_architecture_validator(node, kw):
    g = GameDepLib(kw.get('gamedep_type'))
    return OneOf(g.list_architectures(False))

@deferred
def deferred_edit_dependency_one_widget(node, kw):
    g = GameDepLib(kw.get('gamedep_type'))
    return SelectWidget(values=g.dependency_dropdown(), size=10)

@deferred
def deferred_edit_dependency_one_validator(node, kw):
    g = GameDepLib(kw.get('gamedep_type'))
    return OneOf(g.dependency_dropdown(False))

@deferred
def deferred_edit_dependency_two_widget(node, kw):
    g = GameDepLib(kw.get('gamedep_type'))
    depid = kw.get('depid')
    return RadioChoiceWidget(values=g.revision_dropdown(depid))

@deferred
def deferred_edit_dependency_two_validator(node, kw):
    g = GameDepLib(kw.get('gamedep_type'))
    depid = kw.get('depid')
    return OneOf(g.revision_dropdown(depid, False))

@deferred
def deferred_revision_module_type_widget(node, kw):
    g = GameDepLib(kw.get('gamedep_type'))
    return RadioChoiceWidget(values=g.list_moduletypes())

@deferred
def deferred_revision_module_type_validator(node, kw):
    g = GameDepLib(kw.get('gamedep_type'))
    return OneOf(g.list_moduletypes(False))

class AddPictureSchema(MappingSchema):
    picture = SchemaNode(FileData(), widget=FileUploadWidget(TmpStore()),
                         validator=valid_picture)

class AddSourceSchema(MappingSchema):
    source = SchemaNode(FileData(), widget=FileUploadWidget(TmpStore()),
                        validator=valid_source_file)

class EditGameDepSchema(MappingSchema):
    name = SchemaNode(String(), widget=TextInputWidget(size=40),
                      validator=Regex("^[a-zA-Z_0-9]*$", 
                                      "Only characters a-z A-Z 0-9 _ " + 
                                      "are accepted."))
    display_name = SchemaNode(String(), widget=TextInputWidget(size=40))
    description = SchemaNode(String(), widget=TextAreaWidget(cols=80, rows=20))
    tags = SchemaNode(String(), widget=TextInputWidget(size=40),
                      missing='')
    
class AddBinarySchema(MappingSchema):
    binary = SchemaNode(FileData(), widget=FileUploadWidget(TmpStore()),
                        validator=valid_binary_file)
    operatingsystem = SchemaNode(String(), 
                                 widget=deferred_operating_system_widget,
                                 validator=deferred_operating_system_validator)
    architecture = SchemaNode(String(), widget=deferred_architecture_widget,
                              validator=deferred_architecture_validator)

class EditBinarySchema(MappingSchema):
    binary = SchemaNode(FileData(),
                        widget=FileUploadWidget(TmpStore()),
                        validator=valid_binary_file)

class EditOSArchSchema(MappingSchema):
    operatingsystem = SchemaNode(String(), 
                                 widget=deferred_operating_system_widget,
                                 validator=deferred_operating_system_validator)
    architecture = SchemaNode(String(), widget=deferred_architecture_widget,
                              validator=deferred_architecture_validator)

class EditDependencySchemaOne(MappingSchema):
    dependency = SchemaNode(String(), 
                            widget=deferred_edit_dependency_one_widget,
                            validator=deferred_edit_dependency_one_validator)

class EditDependencySchemaTwo(MappingSchema):
    revision = SchemaNode(String(), widget=deferred_edit_dependency_two_widget,
                          default="-1",
                          validator=deferred_edit_dependency_two_validator)

class EditRevisionSchema(MappingSchema):
    version = SchemaNode(Decimal(), widget=TextInputWidget(size=40))
    module_type = SchemaNode(String(), name="moduletype",
                             widget=deferred_revision_module_type_widget,
                             validator=deferred_revision_module_type_validator)