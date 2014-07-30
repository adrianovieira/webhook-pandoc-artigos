# coding: utf-8
'''
App: Webhook
description: permitir hook de conversão pandoc em "documentos/artigos"
author: Adriano dos Santos Vieira
character encoding: UTF-8
'''
from flask import Flask, request, json
import requests
import ConfigParser
import gitlab

app = Flask(__name__)

'''
pandocParser: realizara a conversão do artigo para PDF

@params:
  p_app_setup: The ID of a project (required)
  p_webhook_data: ID of merge request (required)
  note: Text of comment (required)
'''
def pandocParser(p_app_setup, p_webhook_data):

  converted = False

  if app.debug: print 'APP_Setup:'
  if app.debug: print p_app_setup

  if app.debug: print 'WEBHook_data:'
  if app.debug: print p_webhook_data

  # insere comentário no merge request
  #      "falta <obter-nome-do-artigo>
  app.gitlab.addcommenttomergerequest(webhook_data['object_attributes']['target_project_id'], \
            webhook_data['object_attributes']['id'], \
            'O artigo **'+'<obter-nome-do-artigo>'+'** será convertido!')

  return converted

'''
getConfig: obtem dados de configuracao do ambiente
'''
def getConfig():
  Config = ConfigParser.ConfigParser()
  '''
  obtem dados de configuracao padrao
  '''
  try:
    ok = Config.read('webhook-dist.cfg')
    if not ok: raise
  except:
    app.log_message = "ERROR: trying to read dist-config file."
    return False

  app.setup['gitlab_url'] = Config.get('enviroment', 'gitlab_url')
  app.setup['webhook_user'] = Config.get('enviroment', 'webhook_user')
  app.setup['webhook_pass'] = Config.get('enviroment', 'webhook_pass')
  app.setup['production'] = Config.get('enviroment', 'production')
  app.setup['template_path'] = Config.get('enviroment', 'template_path')
  app.setup['pandoc'] = Config.get('enviroment', 'pandoc')
  app.setup['pdflatex'] = Config.get('enviroment', 'pdflatex')
  app.setup['make'] = Config.get('enviroment', 'make')
  app.setup['DEBUG_LEVEL'] = Config.get('enviroment', 'DEBUG_LEVEL')
  app.setup['DEBUG'] = Config.get('enviroment', 'DEBUG')

  '''
  obtem dados de configuracao personalizados
  '''
  try:
    ok = Config.read('webhook.cfg')
    if not ok: raise
    if Config.get('enviroment', 'gitlab_url'):
      app.setup['gitlab_url'] = Config.get('enviroment', 'gitlab_url')
    if Config.get('enviroment', 'webhook_user'):
      app.setup['webhook_user'] = Config.get('enviroment', 'webhook_user')
    if Config.get('enviroment', 'webhook_pass'):
      app.setup['webhook_pass'] = Config.get('enviroment', 'webhook_pass')
    if Config.get('enviroment', 'production'):
      app.setup['production'] = Config.get('enviroment', 'production')
    if Config.get('enviroment', 'template_path'):
      app.setup['template_path'] = Config.get('enviroment', 'template_path')
    if Config.get('enviroment', 'pandoc'):
      app.setup['pandoc'] = Config.get('enviroment', 'pandoc')
    if Config.get('enviroment', 'pdflatex'):
      app.setup['pdflatex'] = Config.get('enviroment', 'pdflatex')
    if Config.get('enviroment', 'make'):
      app.setup['make'] = Config.get('enviroment', 'make')
    if Config.get('enviroment', 'DEBUG_LEVEL'):
      app.setup['DEBUG_LEVEL'] = Config.get('enviroment', 'DEBUG_LEVEL')
    if Config.get('enviroment', 'DEBUG'):
      app.setup['DEBUG'] = Config.get('enviroment', 'DEBUG')
  except:
    app.log_message = "WARNING: can't read custom-config file."
    print app.log_message
    pass

  return True

'''
CONTANTES
avaliar "modulo: logging"
'''
DEBUG_LEVEL0 = 0
DEBUG_LEVEL1 = 1 # mostra algumas mensagens na console
DEBUG_INTERATIVO = 9 # ipdb ativado: "ipdb.set_trace()"

'''
Gitlab status and merge_status
'''
GL_STATE = {
   'CLOSED':'closed',
   'OPENED':'opened'
   }

GL_STATUS = {
   'merge_request':'merge_request',
   'cannot_be_merged':'cannot_be_merged',
   'can_be_merged':'can_be_merged'
   }

@app.route('/',methods=['GET', 'POST'])
def index():
   app_msg_status = ''
   if request.method == 'GET':
        return 'Aplicacao para webhook! \n Use adequadamente!'

   elif request.method == 'POST':

    if app.setup['DEBUG'] == 'True' and int(app.setup['DEBUG_LEVEL']) == DEBUG_INTERATIVO:
       import ipdb; ipdb.set_trace() # ativado para debug interativo

    webhook_data = json.loads(request.data)

    try:
      app.gitlab = gitlab.Gitlab(app.setup['gitlab_url'])
      if not hasattr(app, 'gitlab'): raise
    except:
      app.log_message = "ERROR: trying to set gitlab url."
      if app.debug: print app.log_message
      return '{"status": "'+app.log_message+'"}'

    try:
      ok = app.gitlab.login(app.setup['webhook_user'], app.setup['webhook_pass'])
      if not ok: raise
    except:
      app.log_message = "ERROR: trying to set gitlab user/pass; or gitlab_url error."
      if app.debug: print app.log_message
      return '{"status": "'+app.log_message+'"}'

    if app.debug: print webhook_data

    try:
      app_msg_status = "not a merge request"
      if webhook_data['object_kind'] or webhook_data['object_attributes']:
        if webhook_data['object_kind'] != GL_STATUS['merge_request']:
          raise

        if webhook_data['object_attributes']:
          if webhook_data['object_attributes']['state'] == GL_STATE['OPENED']:
            if webhook_data['object_attributes']['merge_status'] == GL_STATUS['cannot_be_merged']:
              app_msg_status = "cannot be merged"

              app.gitlab.addcommenttomergerequest(webhook_data['object_attributes']['target_project_id'], \
                        webhook_data['object_attributes']['id'], \
                        'merge não aceito. Verique "branch" e solicite novamente!')
              raise # caso nao possa ser feito merge via gitlab "merge request invalido"
          else:
            app_msg_status = "MR "+webhook_data['object_attributes']['state']+\
                             " - "+webhook_data['object_attributes']['merge_status']
            raise

    except: # IndexError: ou caso nao seja "merge_request"
        if app.debug: print 'Aplicacao webhook para "Merge Request"! \n Use adequadamente!'
        status = '{"status": "ERROR", "message": "'+app_msg_status+'"}'
        return status

    if webhook_data['object_attributes']['state'] == GL_STATE['OPENED'] and \
       webhook_data['object_attributes']['merge_status'] == GL_STATUS['can_be_merged']:
      if app.debug: print "\nProcessing merge request ...\n"

      # simples adição de comentário ao merge request
      app.gitlab.addcommenttomergerequest(webhook_data['object_attributes']['target_project_id'], \
                webhook_data['object_attributes']['id'], \
                'Processing merge request ...['+webhook_data['object_attributes']['merge_status']+']')

      # realisar a conversao de artigo para PDF
      pandocParser(app.setup, webhook_data)

    return '{"status": "OK"}'

@app.errorhandler(500)
def internal_error(error):

    return '{"status": "500 error"}'

'''
Inicia aplicação
'''
app.setup = {} # global de configuracao

if __name__ == '__main__':
  if getConfig(): # obtem dados de configuracao inicial
    if app.setup['DEBUG'] == 'True':
      app.debug = True
      app.run(host='0.0.0.0')
    else:
      app.run()
  else:
    print app.log_message #"ERROR: trying to read dist-config file."
