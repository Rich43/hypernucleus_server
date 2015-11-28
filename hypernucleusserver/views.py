from string import capwords

from deform.exception import ValidationFailure
from deform.form import Form
from pyracms.lib.helperlib import get_username, redirect, rapid_deform
from pyracms.lib.settingslib import SettingsLib
from pyracms.lib.userlib import UserLib
from pyracms.views import INFO, ERROR
from pyramid.exceptions import NotFound
from pyramid.httpexceptions import HTTPFound, HTTPForbidden
from pyramid.security import has_permission
from pyramid.url import route_url, current_route_url
from pyramid.view import view_config
from pyracms.models import DBSession
import pyracms.lib.taglib as taglib

from .deform_schemas.gamedep import (EditGameDepSchema, AddSourceSchema,
                                     AddBinarySchema, EditBinarySchema,
                                     EditOSArchSchema,
                                     EditDependencySchemaOne,
                                     EditDependencySchemaTwo,
                                     EditRevisionSchema)
from .lib.gamedeplib import (AlreadyVoted, GAME, DEP, GameDepLib,
                             GameDepNotFound, GameDepFound, BinaryNotFound,
                             SourceCodeNotFound)
from .lib.outputlib import OutputLib
from .models import GameDepTags

u = UserLib()
s = SettingsLib()

def check_owner(context, request):
    page_id = request.matchdict.get('page_id')
    gamedeptype = request.matchdict.get('type')
    g = GameDepLib(gamedeptype)
    try:
        page = g.show(page_id)
        if (has_permission('gamedep_mod', context, request) or
            page.owner == u.show(get_username(request))):
            return True
        else:
            raise HTTPForbidden
    except GameDepNotFound:
        return True

def get_pageid_revision(request):
    """
    Get page_id and revision from matchdict
    """
    page_id = request.matchdict.get('page_id')
    revision = request.matchdict.get('revision')
    return (page_id, revision)


@view_config(route_name='outputs_xml')
def output_xml(context, request):
    """
    Output serialized xml data
    """
    olib = OutputLib(request)
    res = request.response
    res.content_type = "application/xml"
    res.body = olib.show_xml()
    return res


@view_config(route_name='outputs_json')
def output_json(context, request):
    """
    Output serialized json data
    """
    olib = OutputLib(request)
    res = request.response
    res.content_type = "application/json"
    res.body = olib.show_json().encode()
    return res


@view_config(route_name='gamedeplist', permission='gamedep_list',
             renderer='gamedep/list.jinja2')
def gamedep_list(context, request):
    gamedeptype = request.matchdict.get('type')
    g = GameDepLib(gamedeptype)
    gamedeptypetwo = {GAME: "game",
                      DEP: "dependenc"}.get(gamedeptype)
    return {'pages': g.list(), 'type': gamedeptype,
            'captype': capwords(gamedeptypetwo),
            "gamedeptypetwo": gamedeptypetwo}


@view_config(route_name='gamedep_published', permission='gamedep_publish')
def gamedep_published(context, request):
    gamedeptype = request.matchdict.get('type')
    g = GameDepLib(gamedeptype)
    page_id = request.matchdict.get('page_id')
    revision = request.matchdict.get('revision')
    check_owner(context, request)
    try:
        g.flip_published(page_id, revision)
    except BinaryNotFound:
        request.session.flash(s.show_setting("ERROR_NOT_UPLOADED_BINARY"),
                              ERROR)
    except SourceCodeNotFound:
        request.session.flash(s.show_setting("ERROR_NOT_UPLOADED_SOURCE_CODE"),
                              ERROR)
    return HTTPFound(location=route_url("gamedep_item", request,
                                        type=gamedeptype,
                                        page_id=page_id))


@view_config(route_name='gamedep_item', renderer='gamedep/item.jinja2',
             permission='gamedep_view')
def gamedep_item(context, request):
    gamedeptype = request.matchdict.get('type')
    g = GameDepLib(gamedeptype)
    page_id = request.matchdict.get('page_id')
    revision = request.matchdict.get('revision')
    try:
        dbpage, dbrevision = g.show(page_id, revision, False)
        result = {'page_id': page_id, 'revision': revision,
                  'dbpage': dbpage, 'dbrevision': dbrevision,
                  'type': gamedeptype, "thread_enabled": False}
        if dbpage.thread_id != -1:
            from pyracms_forum.views import get_thread
            result.update(get_thread(context, request, dbpage.thread_id))
            result.update({"thread_enabled": True})
        return result
    except GameDepNotFound:
        return HTTPFound(location=route_url("gamedep_edit",
                                            request, type=gamedeptype,
                                            page_id=page_id))


@view_config(route_name='gamedep_edit', permission='gamedep_edit',
             renderer='gamedep/edit.jinja2')
def gamedep_edit(context, request):
    check_owner(context, request)
    def gamedep_edit_submit(context, request, deserialized, bind_params):
        page_id = get_pageid_revision(request)[0]
        gamedeptype = request.matchdict.get('type')
        g = GameDepLib(gamedeptype)
        name = deserialized.get("name")
        display_name = deserialized.get("display_name")
        description = deserialized.get("description")
        tags = deserialized.get("tags")
        if g.exists(page_id):
            g.update(page_id, name, display_name, description, tags)
            request.session.flash(s.show_setting("INFO_UPDATED")
                                  % page_id, INFO)
        else:
            g.create(name, display_name, description, tags,
                     u.show(get_username(request)), request)
            request.session.flash(s.show_setting("INFO_CREATED")
                                  % page_id, INFO)
        return redirect(request, "gamedep_item", page_id=name,
                        type=gamedeptype)

    gamedeptype = request.matchdict.get('type')
    g = GameDepLib(gamedeptype)
    page_id = request.matchdict.get('page_id')
    t = taglib.TagLib(GameDepTags, taglib.GAMEDEP)
    try:
        dbpage = g.show(page_id)[0]
        dbdescription = dbpage.description
        dbname = dbpage.name
        dbdisplay_name = dbpage.display_name
    except GameDepNotFound:
        dbpage = None
        dbdescription = ""
        dbname = page_id
        dbdisplay_name = ""
    return rapid_deform(context, request, EditGameDepSchema,
                        gamedep_edit_submit, name=dbname,
                        display_name=dbdisplay_name,
                        description=dbdescription,
                        tags=t.get_tags(dbpage))


@view_config(route_name='gamedep_delete', permission='gamedep_delete')
def gamedep_delete(context, request):
    check_owner(context, request)
    page_id = request.matchdict.get('page_id')
    gamedeptype = request.matchdict.get('type')
    g = GameDepLib(gamedeptype)
    if g.exists(page_id):
        g.delete(page_id, request)
        request.session.flash(s.show_setting("INFO_DELETED") % page_id, INFO)
    else:
        request.session.flash(s.show_setting("ERROR_NOT_FOUND")
                              % page_id, ERROR)
    return redirect(request, "gamedeplist", type=gamedeptype)


@view_config(route_name='gamedep_add_src', permission='gamedep_add_source',
             renderer='gamedep/edit.jinja2')
def gamedep_add_source(context, request):
    check_owner(context, request)
    def gamedep_add_source_submit(context, request, deserialized,
                                  bind_params):
        page_id, revision = get_pageid_revision(request)
        gamedeptype = request.matchdict.get('type')
        g = GameDepLib(gamedeptype)
        source = deserialized.get("source")
        g.create_source(page_id, revision, source['fp'],
                        source['mimetype'], source['filename'],
                        request)
        request.session.flash(s.show_setting("INFO_SOURCE_UPLOADED")
                              % source['filename'], INFO)
        return redirect(request, "gamedep_item", page_id=page_id,
                        type=gamedeptype)

    gamedeptype = request.matchdict.get('type')
    g = GameDepLib(gamedeptype)
    page_id = request.matchdict.get('page_id')
    revision = request.matchdict.get('revision')
    moduletype = g.show(page_id, revision)[1].moduletype

    # Block people from adding source to a dependency
    if gamedeptype != "game":
        return NotFound(request.url)

    # Figure out required files/folders
    req_file_folder = []
    if moduletype == "file":
        req_file_folder.append("%s/%s.py" % (page_id, page_id))
    else:
        req_file_folder.append("%s/__init__.py" % page_id)

    return rapid_deform(context, request, AddSourceSchema,
                        gamedep_add_source_submit,
                        req_file_folder=req_file_folder)


@view_config(route_name='gamedep_add_bin',
             renderer='gamedep/edit.jinja2',
             permission='gamedep_add_binary')
@view_config(route_name='gamedep_edit_bin',
             renderer='gamedep/edit.jinja2',
             permission='gamedep_edit_binary')
def gamedep_add_binary(context, request):
    check_owner(context, request)
    gamedeptype = request.matchdict.get('type')
    g = GameDepLib(gamedeptype)
    page_id = request.matchdict.get('page_id')
    binary_id = request.matchdict.get('binary_id')
    revision = request.matchdict.get('revision')
    edittype = request.matchdict.get('edittype')

    try:
        bin_obj = g.show_binary(binary_id)
    except GameDepNotFound:
        bin_obj = None

    if binary_id and edittype:
        pass

    # Initialise form library
    if not binary_id and not edittype:
        schema = AddBinarySchema()
    elif binary_id and edittype == "1":
        schema = EditBinarySchema()
    elif binary_id and edittype == "2":
        schema = EditOSArchSchema()
    else:
        request.session.flash(s.show_setting("ERROR_INVALID_BINARY_ID"), ERROR)
        return redirect(request, "gamedep_item", page_id=page_id,
                        type=gamedeptype)

    schema = schema.bind(gamedep_type=gamedeptype, bin_obj=bin_obj,
                         req_file_folder=["%s/" % page_id])
    myform = Form(schema, buttons=['submit'])
    reqts = myform.get_widget_resources()

    if 'submit' in request.POST:
        controls = request.POST.items()
        try:
            deserialized = myform.validate(controls)
        except ValidationFailure as e:
            # Failed validation
            return {'page_id': page_id, 'form': e.render(),
                    'js_links': reqts['js']}

        # Form submitted, all validated!
        binary = deserialized.get("binary")
        operatingsystem = deserialized.get("operatingsystem")
        architecture = deserialized.get("architecture")
        if not binary_id and not edittype:
            g.create_binary(page_id, revision, operatingsystem, architecture,
                            binary['fp'], binary['mimetype'],
                            binary['filename'], request)
            request.session.flash(s.show_setting("INFO_BINARY_ADDED")
                                  % binary['filename'], INFO)
        else:
            g.update_binary(page_id, revision, binary_id, operatingsystem,
                            architecture, binary, request)
            request.session.flash(s.show_setting("INFO_BINARY_UPDATED")
                                  % binary['filename'], INFO)
        return redirect(request, "gamedep_item", page_id=page_id,
                        type=gamedeptype)
    # Display default form
    return {'page_id': page_id, 'form': myform.render(),
            'js_links': reqts['js']}


@view_config(route_name='gamedep_del_bin',
             permission='gamedep_delete_binary')
def gamedep_delete_binary(context, request):
    check_owner(context, request)
    gamedeptype = request.matchdict.get('type')
    binid = request.matchdict.get('binary_id')
    g = GameDepLib(gamedeptype)
    page_id = request.matchdict.get('page_id')
    revision = request.matchdict.get('revision')
    try:
        with DBSession.no_autoflush:
            bin_name = g.show_binary(binid).file_obj.name
            g.delete_binary(page_id, revision, binid)
            request.session.flash(s.show_setting("INFO_BINARY_DELETED")
                                  % bin_name, INFO)
    except GameDepNotFound:
        request.session.flash(s.show_setting("ERROR_NOT_FOUND")
                              % page_id, ERROR)
    return redirect(request, "gamedep_item", page_id=page_id,
                    type=gamedeptype)


@view_config(route_name='gamedep_add_dep',
             permission='gamedep_add_dependency',
             renderer='gamedep/edit.jinja2')
@view_config(route_name='gamedep_add_deptwo',
             renderer='gamedep/edit.jinja2',
             permission='gamedep_add_dependency')
def gamedep_add_dependency(context, request):
    check_owner(context, request)
    def gamedep_add_dependency_submit(context, request, deserialized,
                                      bind_params):
        gamedeptype = request.matchdict.get('type')
        g = GameDepLib(gamedeptype)
        page_id = request.matchdict.get('page_id')
        dep_id = request.matchdict.get('depid')
        form_rev_id = deserialized.get("revision")
        form_dep_id = deserialized.get("dependency")
        if not form_rev_id:
            return HTTPFound(location=current_route_url(request)
                                      + "/%s" % form_dep_id)
        else:
            if form_rev_id == "-1":
                g.create_dependency(page_id, dep_id)
            else:
                g.create_dependency(page_id, dep_id, form_rev_id)
            dep_name = g.show_dependency(g.show(page_id,
                                                no_revision_error=False)[0],
                                         dep_id).page.name
            request.session.flash(s.show_setting("INFO_DEPENDENCY_ADDED")
                                  % dep_name, INFO)
            return redirect(request, "gamedep_item", page_id=page_id,
                            type=gamedeptype)

    depid = request.matchdict.get('depid')
    gamedeptype = request.matchdict.get('type')
    if not depid:
        schema = EditDependencySchemaOne
    else:
        schema = EditDependencySchemaTwo
    return rapid_deform(context, request, schema,
                        gamedep_add_dependency_submit,
                        gamedep_type=gamedeptype, depid=depid)


@view_config(route_name='gamedep_del_dep',
             renderer='gamedep/item.jinja2',
             permission='gamedep_delete_dependency')
def gamedep_delete_dependency(context, request):
    check_owner(context, request)
    gamedeptype = request.matchdict.get('type')
    depid = request.matchdict.get('depid')
    g = GameDepLib(gamedeptype)
    page_id = request.matchdict.get('page_id')
    try:
        dep_name = g.show_dependency(g.show(page_id)[0],
                                     depid).page_obj.name
        g.delete_dependency(page_id, depid)
        request.session.flash(s.show_setting("INFO_DEPENDENCY_DELETED")
                              % dep_name, INFO)
    except GameDepNotFound:
        request.session.flash(s.show_setting("ERROR_NOT_FOUND")
                              % page_id, ERROR)
    return redirect(request, "gamedep_item", page_id=page_id,
                    type=gamedeptype)


@view_config(route_name='gamedep_edit_revision',
             permission='gamedep_edit_revision',
             renderer='gamedep/edit.jinja2')
@view_config(route_name='gamedep_edit_revision2',
             renderer='gamedep/edit.jinja2',
             permission='gamedep_edit_revision')
def gamedep_edit_revision(context, request):
    check_owner(context, request)
    def gamedep_edit_revision_submit(context, request, deserialized,
                                     bind_params):
        page_id, revision = get_pageid_revision(request)
        gamedeptype = request.matchdict.get('type')
        g = GameDepLib(gamedeptype)
        frmversion = deserialized.get("version")
        frmmodule_type = deserialized.get("moduletype")
        if bind_params['update']:
            g.update_revision(page_id, revision, frmversion, frmmodule_type)
            request.session.flash(s.show_setting("INFO_REVISION_UPDATED")
                                  % (frmversion, page_id), INFO)
        else:
            try:
                g.create_revision(page_id, frmversion, frmmodule_type)
                request.session.flash(s.show_setting("INFO_REVISION_CREATED")
                                        % (frmversion, page_id), INFO)
            except GameDepFound:
                request.session.flash(s.show_setting("ERROR_FOUND")
                                        % frmversion, ERROR)

        return redirect(request, "gamedep_item", page_id=page_id,
                        type=gamedeptype)

    gamedeptype = request.matchdict.get('type')
    g = GameDepLib(gamedeptype)
    page_id = request.matchdict.get('page_id')
    revision = request.matchdict.get('revision')
    update = False
    if revision:
        update = True
        dbrevision = g.show(page_id, revision)[1]
        dbversion = dbrevision.version
        dbmoduletype_name = dbrevision.moduletype
    else:
        dbrevision = None
        dbversion = 0.1
        dbmoduletype_name = "file"
    return rapid_deform(context, request, EditRevisionSchema,
                        gamedep_edit_revision_submit,
                        version=dbversion, moduletype=dbmoduletype_name,
                        gamedep_type=gamedeptype, update=update)


@view_config(route_name='gamedep_delete_revision',
             permission='gamedep_delete')
def gamedep_delete_revision(context, request):
    check_owner(context, request)
    page_id = request.matchdict.get('page_id')
    revision = request.matchdict.get('revision')
    gamedeptype = request.matchdict.get('type')
    g = GameDepLib(gamedeptype)
    if g.exists(page_id):
        caption = "Version %s" % g.show(page_id, revision)[1].version
        try:
            g.delete_revision(page_id, revision, request)
            request.session.flash(s.show_setting("INFO_DELETED")
                                  % caption, INFO)
        except GameDepNotFound:
            request.session.flash(s.show_setting("ERROR_NOT_FOUND")
                                  % page_id, ERROR)
    else:
        request.session.flash(s.show_setting("ERROR_NOT_FOUND")
                              % page_id, ERROR)
    return redirect(request, "gamedep_item", page_id=page_id,
                    type=gamedeptype)


@view_config(route_name='gamedep_add_vote', permission='vote')
def gamedep_add_vote(context, request):
    """
    Add a vote to a gamedep
    """
    vote_id = request.matchdict.get('vote_id')
    like = request.matchdict.get('like').lower() == "true"
    gamedeptype = request.matchdict.get('type')
    gd_lib = GameDepLib(gamedeptype)
    gd = gd_lib.show(vote_id, no_revision_error=False)[0]
    try:
        gd_lib.add_vote(gd, u.show(get_username(request)), like)
        request.session.flash(s.show_setting("INFO_VOTE"), INFO)
    except AlreadyVoted:
        request.session.flash(s.show_setting("ERROR_VOTE"), ERROR)
    return redirect(request, "article_read", page_id=vote_id)
