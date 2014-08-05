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

# ipdb: inclusão desse módulo é autorealizada na função "index()"

app = Flask(__name__)

'''
gitCheckout: obtem "branch" de repositorio de "documentos/artigos"

@params:
  p_target_project_id: The ID of a project (required)
  p_mergerequest_id: ID of merge request (required)
  p_git_branch: "branch" do artigo para conversão em PDF (required)
'''
def gitCheckout(p_target_project_id, p_mergerequest_id, p_mergerequest_branch):

  result = False

  if app.debug: print 'mergerequest_branch:'
  if app.debug: print p_mergerequest_branch

  # <obter-nome-do-artigo> == BRANCH
  mergerequest_comment = u"A ***branch* [%s]** e artigo serão obtidos do repositório!" % p_mergerequest_branch

  app.log_message = mergerequest_comment
  if app.debug: print app.log_message

  # insere comentário no merge request
  app.gitlab.addcommenttomergerequest(p_target_project_id, \
                                      p_mergerequest_id, mergerequest_comment)

  return result

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

abtidos dos arquivos:
webhook-dist.cfg - padrão para o "webhook" (obrigatório)
webhook.cfg - personalizado para o ambiente de trabalho/produção (opcional)
'''
def getConfig():
  Config = ConfigParser.ConfigParser()

  '''
  # obtem dados de configuracao padrao
  '''
  try:
    ok = Config.read('webhook-dist.cfg')
    if not ok: raise
  except:
    app.log_message = "ERROR: trying to read dist-config file."
    return False

  app.setup['gitlab_url'] = Config.get('enviroment', 'gitlab_url')
  app.setup['gitlab_target_branch'] = Config.get('enviroment', 'gitlab_target_branch')
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
    if Config.get('enviroment', 'gitlab_target_branch'):
      app.setup['gitlab_target_branch'] = Config.get('enviroment', 'gitlab_target_branch')
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
constantes para comparação com o webhook
'''
GL_STATE = {
   'CLOSED':'closed',
   'OPENED':'opened',
   'REOPENED':'reopened'
   }

GL_STATUS = {
   'merge_request':'merge_request',
   'cannot_be_merged':'cannot_be_merged',
   'can_be_merged':'can_be_merged'
   }

@app.route('/',methods=['GET', 'POST'])
def index():

  if request.method == 'GET':
    return 'Aplicacao para webhook! \n Use adequadamente!'

  elif request.method == 'POST':

    if app.setup['DEBUG'] == 'True' and int(app.setup['DEBUG_LEVEL']) == DEBUG_INTERATIVO:
       import ipdb; ipdb.set_trace() # ativação de debug interativo

    # abtem dados do webhook gitlab
    webhook_data = json.loads(request.data)

    if app.debug: print webhook_data

    # abre conexao com servidor gitlab
    try:
      app.gitlab = gitlab.Gitlab(app.setup['gitlab_url'])
      if not hasattr(app, 'gitlab'): raise
    except:
      app.log_message = "ERROR: trying to set gitlab url."
      if app.debug: print app.log_message
      return '{"status": "'+app.log_message+'"}'

    # autentica na servidor gitlab
    try:
      ok = app.gitlab.login(app.setup['webhook_user'], app.setup['webhook_pass'])
      if not ok: raise
    except:
      app.log_message = "ERROR: trying to set gitlab user/pass; or gitlab_url error."
      if app.debug: print app.log_message
      return '{"status": "'+app.log_message+'"}'

    # avalia webhook iniciado pelo gitlab
    try:
      app.log_message = "not a merge request"
      if webhook_data['object_kind'] or webhook_data['object_attributes']:
        if webhook_data['object_kind'] != GL_STATUS['merge_request']:
          raise

        if webhook_data['object_attributes']:
          if webhook_data['object_attributes']['target_branch'] != app.setup['gitlab_target_branch']:
            app.log_message = "target branch not allowed"
            raise

          if webhook_data['object_attributes']['state'] == GL_STATE['REOPENED']:
            app.log_message = "reopen not allowed for a merge request"
            raise # não trata reopened, pois esse modo não inclui novos commits

          if webhook_data['object_attributes']['state'] == GL_STATE['OPENED']:
            if webhook_data['object_attributes']['merge_status'] == GL_STATUS['cannot_be_merged']:
              app.log_message = "cannot be merged"

              app.gitlab.addcommenttomergerequest(webhook_data['object_attributes']['target_project_id'], \
                        webhook_data['object_attributes']['id'], \
                        '*merge* não aceito. Verique *branch* e solicite novamente!')
              raise # caso nao possa ser feito merge via gitlab "merge request invalido"
          else:
            app.log_message = "merge request "+webhook_data['object_attributes']['state']+\
                             " - "+webhook_data['object_attributes']['merge_status']
            raise

    except: # array IndexError: ou caso nao seja "merge_request"
        status = '{"status": "ERROR", "message": "'+app.log_message+'"}'
        if app.debug: print 'Aplicacao webhook para "Merge Request"! \n Use adequadamente!'
        if app.debug: print "ERROR: "+app.log_message
        return status

    # processa o webhook para "merge request"
    status = '{"status": "nOK"}'
    app.log_message = '{"type": "WARNING", "message": "processing"}'
    if webhook_data['object_attributes']['state'] == GL_STATE['OPENED'] and \
       webhook_data['object_attributes']['merge_status'] == GL_STATUS['can_be_merged']:
      if app.debug: print "\nProcessing merge request ...\n"
      if app.debug: print app.log_message

      # simples adição de comentário ao merge request
      app.gitlab.addcommenttomergerequest(webhook_data['object_attributes']['target_project_id'], \
                                          webhook_data['object_attributes']['id'], \
                                          'Processando *merge request* ...[*'+ \
                                          webhook_data['object_attributes']['merge_status']+'*]')

      # obtem do repositório a branch a converter para PDF
      if gitCheckout(webhook_data['object_attributes']['target_project_id'], \
                     webhook_data['object_attributes']['id'], \
                     webhook_data['object_attributes']['source_branch']):
        # realisar a conversao de artigo para PDF
        if pandocParser(app.setup, webhook_data):
           status = '{"status": "OK"}'

    return status

# trata erro http/500, mesmo quando em modo debug=true
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
