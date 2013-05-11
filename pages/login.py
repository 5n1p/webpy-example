#!/usr/bin/python

import os
import sys
import web
import json

import mimerender

import wputil
import wpauth
import accountdb

mimerender = mimerender.WebPyMimeRender()

log = wputil.Log('login')

login_form = web.form.Form(
  web.form.Hidden("backto", description="URL to return to"),
  web.form.Textbox("username", web.form.notnull, description="Username"),
  web.form.Password("password", web.form.notnull, description="Password"),
  web.form.Button("submit", type="submit", html="Login"),
  web.form.Button("cancel", type="cancel", html="Cancel"),
)

# Instantiate HTML templates
htmlout = web.template.render( 'templates/', base='layout' )

render_html = lambda **kwargs: htmlout.login( kwargs )
render_json = lambda **kwargs: json.dumps( kwargs, cls=wputil.CustomEncoder )

# These are the URLs we watch for. We don't see the prepended /login portion
# in this module because the index.py runs us as a subapplication.
urls = (
  '',      wputil.slashy,
  '/rest', 'rest_login',
  '/',     'login'
)

class login:
  """
  The login class
  """

  @mimerender(
    default = 'html',
    override_input_key = 'format',
    html = render_html
  )
  def GET( self ):
    log.loggit( 'login.GET()' )
    f = login_form()
    wi = web.input()
    if wi.has_key('backto'):
      f.backto.set_value( wi.backto )
    results = { 'status' : 'success',
                'message' : 'Please provide a username and a password to login.',
                'form' : f }
    return results


  @mimerender(
    default = 'html',
    override_input_key = 'format',
    html = render_html
  )
  def POST( self ):
    log.loggit( 'login.POST()' )

    # Check to see if we are canceling out
    if web.input().has_key('cancel'):
      raise web.seeother( '/', absolute=True )

    # Validate the form
    f = login_form()
    if not f.validates():
      return { 'status' : 'error',
               'message' : 'Verify all information has been provided correctly.',
               'form' : f }

    # Get the account credentials
    adb = accountdb.AccountDB()
    try:
      result = adb.login( f.d.username, f.d.password )
    except Exception, e:
      return { 'status' : 'error',
               'message' : 'An error occurred: %s' % e }

    # If it isn't an account...
    if not result:
      return { 'status' : 'failure',
               'message' : 'Login failed' }

    redir = '/'
    if f.d.backto != '':
      redir = f.d.backto
    raise web.seeother( redir, absolute=True )


class rest_login:
  """
  The rest_login class
  """

  @wpauth.oauth_protect
  @mimerender(
    default = 'json',
    override_input_key = 'format',
    json = render_json
  )
  def POST( self ):
    log.loggit( 'rest_login.POST()' )

    wi = web.input()

    # Get the account credentials
    adb = accountdb.AccountDB()
    try:
      result = adb.login( wi['username'], wi['password'] )
    except Exception, e:
      return { 'status' : 'error',
               'message' : 'An error occurred: %s' % e }

    # If we failed our login or the account doesn't exist.
    if not result:
      return { 'status' : 'failure',
               'message' : 'Login failed',
               'session_id' : web.ctx.session['session_id'] }

    return { 'status' : 'success',
             'message' : 'Login successful',
             'session_id' : web.ctx.session['session_id'] }


app_login = web.application( urls, locals() )

# End
