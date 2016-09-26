def includeme(config):
    """ Activate the forum; usually called via
    ``config.include('pyracms_forum')`` instead of being invoked
    directly. """
    config.include('pyramid_jinja2')
    config.add_jinja2_search_path("hypernucleusserver:templates")
    # Outputs routes
    config.add_route('outputs_xml', '/outputs/xml')
    config.add_route('outputs_file', '/outputs/file/{fileid}')
    config.add_route('outputs_json', '/outputs/json')
    
    # Games/Dependency Routes
    config.add_route('gamedep_add_dep', '/gamedep/{type}/adddep/{page_id}')
    config.add_route('gamedep_add_bin', 
                     '/gamedep/{type}/addbin/{page_id}/{revision}')
    config.add_route('gamedep_edit_bin', 
                     '/gamedep/{type}/editbin/{page_id}' + \
                     '/{revision}/{binary_id}/{edittype}')
    config.add_route('gamedep_del_dep', 
                     '/gamedep/{type}/deldep/{page_id}/{depid}')
    config.add_route('gamedep_delete', '/gamedep/{type}/delete/{page_id}')
    config.add_route('gamedep_add_src', 
                     '/gamedep/{type}/addsrc/{page_id}/{revision}')
    config.add_route('gamedep_edit_revision', 
                     '/gamedep/{type}/edit_revision/{page_id}')
    config.add_route('gamedep_item', '/gamedep/{type}/item/{page_id}')
    config.add_route('gamedep_edit_revision2', 
                     '/gamedep/{type}/edit_revision/{page_id}/{revision}')
    config.add_route('gamedep_delete_revision', 
                     '/gamedep/{type}/delete_revision/{page_id}/{revision}')
    config.add_route('gamedep_add_deptwo', 
                     '/gamedep/{type}/adddep/{page_id}/{depid}')
    config.add_route('gamedeplist', '/gamedep/{type}/list')
    config.add_route('gamedep_edit', '/gamedep/{type}/edit/{page_id}')
    config.add_route('gamedep_published', 
                     '/gamedep/{type}/published/{page_id}/{revision}')
    config.add_route('gamedep_del_bin', 
                     '/gamedep/{type}/delbin/{page_id}/{revision}/{binary_id}')
    config.add_route('gamedep_add_vote', 
                     '/vote/gamedep/{type}/{vote_id}/{like}')
    config.scan('hypernucleusserver.views')
    config.scan('hypernucleusserver.web_service_views')
