# coding: utf-8

'''
Class: VerificaMetadados
description: realizar a verificação de artigos produzidos observando existência de metadados de autor e referências bibliográficas
author: Adriano dos Santos Vieira <adriano.vieira@dataprev.gov.br>
character encoding: UTF-8

@params: (opcional) file_name = nome de arquivo markdown a ser verificado
'''
class VerificaMetadados:

    def __init__(self, file_name=''):
        self.__has_dados_autor= False
        self.__has_dados_referencias = False
        if len(file_name) > 0:
           self.__file_name = file_name
           self.verificaMetadados(self.__file_name)
        else:
           self.__file_name = ''

    def hasDadosAutor(self):
        return self.__has_dados_autor
    def hasDadosReferencias(self):
        return self.__has_dados_referencias


    # @params: file_name = nome de arquivo markdown a ser verificado
    def verificaMetadados(self, file_name=''):

        self.__has_dados_autor= False
        self.__has_dados_referencias = False

        if (len(file_name) == 0) and (len(self.__file_name) > 0):
           file_name = self.__file_name

        __has_autor_group = False
        __has_autor_abstract = False
        __has_referencias_group = False
        __has_referencias_id = False

        with open(file_name) as file:
            while True:  # loop para ler conteudo do arquivo
                line = file.readline()
                if not line:
                   break

                #  verifica metadados de autor
                if (line.find('author:') == 0):
                   __has_autor_group = True

                if (line.find('abstract:') == 0):
                   __has_autor_abstract = True

                #  verifica metadados de referencias
                if (line.find('references:') == 0):
                   __has_referencias_group = True

                if (line.find('- id:') == 0):
                   __has_referencias_id = True

        file.close()

        #  pelo menos dois campos de cada grupo de metadados devem existir
        if (__has_autor_group) and (__has_autor_abstract):
           self.__has_dados_autor= True
        
        if (__has_referencias_group) and (__has_referencias_id):
           self.__has_dados_referencias = True

