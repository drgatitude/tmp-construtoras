#coding: utf-8
# py pesqSistemaConstrutoras.py
# checklist construtoras
# https://trello.com/c/fB4t6bu0/83750-cliente-assina-hoje-%E2%9B%94-brzportal-recanto-das-alpinasmarinalva-do-nascimento-pereira104367117-02valida%C3%A7%C3%A3o-da-pasta
#import requests
from x9 import x9, mylogging
import requests
#import api_trello_class as atrc
import api_tr_cl as atrc
import api_portal as apt
import api_firebase as afb
import time
from datetime import datetime, timezone, timedelta
import bpm
import fluig
import dados
import forcasa
import homelendReq
import tenda
import sicaq

QUADRO = 'Operação' # 'TrelloTest'#
LISTID = dados.LISTID 
LISTIDPENDENCIA = dados.LISTIDPENDENCIA
LISTFINALIZADOSBOARDOPERACAO = dados.LISTFINALIZADOSBOARDOPERACAO
checkListidPadraoAnaliseModelo = dados.checkListidPadraoAnaliseModelo
DIASAPESQUISAR = 30

config = {'apikey':dados.trelloApiKey,'token':dados.trelloToken}
quadroOperacao = atrc.Trello_Board(QUADRO,config)
sistForCasa = forcasa.Forcasa()
sistTenda = tenda.Tenda()



MSG_ROBO_DESLIGADO = 'ROBO {} DESLIGADO pelo firebase :'
VERSAO = 'mainconstrutoras - versao 17/05/21'

PAC_MRV_PNG = dados.PAC_MRV_PNG

portal = afb.get_document_by_name_from_collection('configSistemaConstrutoras', 'portal')
configPortal = {
    'login':portal.get('login'),
    'password':portal.get('senha')
}
portalApp = apt.Portal(configPortal)
'intervalo de 5 minutos'

print(datetime.now(timezone.utc).isoformat())
print(datetime.now(timezone(timedelta(hours=-2))).isoformat())

def main():
    print(VERSAO)
    time.sleep(2)
    fluigsession = requests.Session()
    horaInicio = 6
    horaFim = 22
    while True:
        print("main loop")
        try:
            configGerais = afb.get_document_by_name_from_collection('configSistemaConstrutoras', 'gerais')
            INTERVALO = configGerais.get('intervalo','600')
            FUSO = configGerais.get('fuso','3')
            horaInicioFirebase = configGerais.get('horaInicio','6')
            horaFimFirebase = configGerais.get('horaFim','22')
        except Exception as e:
            x9('EXCEPT MAIN LOOP get data FIREBASE: ' + str(e))
            mylogging(str(e))
            horaInicioFirebase, horaFimFirebase = 7, 22
            # declaro aqui para evitar exception caso de erro no get document do firebase
            INTERVALO = 300
            FUSO = 3
        try:
            datenow = datetime.now()
            print(datenow)
            try:
                horaBR = datenow.hour - int(FUSO)
                horaInicio = int(horaInicioFirebase)
                horaFim = int(horaFimFirebase)
            except Exception as e:
                x9('EXCEPT FUSO, corrigir fuso sistemaConstrutoras: ' + str(e))
                print('-------------------------------- EXCEPT FUSO------')
                print(str(e))
                time.sleep(3)
                horaBR = datenow.hour - 3
            if horaBR >= horaInicio and horaBR <= horaFim:
                #### FC PRINCIPAL #########
                print('===== entrando em mainloop =======')
                data = {'atualizacao': datetime.now(), 'status': 'online', 'info': 'em operacao'}
                afb.update_collection('botsStatus', 'sistemaConstrutoras', data)
                mainloop(fluigsession, FUSO)
            else:
                print('---- NAO eh hora para executar o script')
                data = {'atualizacao': datetime.now(), 'status': 'online', 'info': 'fora do horario execucao'}
                afb.update_collection('botsStatus', 'sistemaConstrutoras', data)
        except Exception as e:
            print("===================x====================")
            x9('EXCEPT MAIN LOOP: ' +str(e))
            print('Exception sistemaConstrutoras: ' + str(e))
            print("===================x====================")
            data = {'atualizacao': datetime.now(), 'status': 'except', 'info': str(e)}
            afb.update_collection('botsStatus', 'sistemaConstrutoras', data)
        time.sleep(10)
        try:
            intervaloInt = int(INTERVALO)
        except:
            intervaloInt = 600
        #trello demora 1min para refletir novos cartoes para aparecerem na busca
        print('aguardadando intervalo de ' + str(intervaloInt))
        print(datetime.now())
        #time.sleep(intervaloTotal)
        for i in range(1,intervaloInt):
            time.sleep(1)
            print('ainda faltam ' + str(intervaloInt - i) +' segundos   ', end='\r')


def mainloop(fluigsession, FUSO):
    # checa fluig, se houver proposta pesquisar no trello, se nao houver, pesquisa no portal (pendencia ou pasta nova)
    print('inicio main loop')
    try:
        acessos = afb.get_document_by_name_from_collection('configSistemaConstrutoras', 'acesso')
        bpmLogin = acessos.get('bpmLogin')
        bpmPassword = acessos.get('bpmSenha')
        fluigLogin = acessos.get('fluigLogin')
        fluigPassword = acessos.get('fluigSenha')
        forCasaLogin = acessos.get('forCasaLogin')
        forCasaSenha = acessos.get('forCasaSenha')
        homelendLogin = acessos.get('homelendLogin')
        homelendSenha = acessos.get('homelendSenha')
        tendaLogin = acessos.get('tendaLogin')
        tendaSenha = acessos.get('tendaSenha')
        executarBPM = acessos.get('executarBPM', 'SIM')
        executarFluig = acessos.get('executarFluig', 'SIM')
        executarForCasa = acessos.get('executarForCasa', 'SIM')
        executarHomelend = acessos.get('executarHomelend', 'SIM')
        executarTenda = acessos.get('executarTenda', 'SIM')
        sicaq_dict = {}
        sicaq_dict['login'] = acessos.get('cxaquilogin')
        sicaq_dict['senha'] = acessos.get('cxaquisenha')
        sicaq_dict['convenio'] = acessos.get('cxaquiconvenio')
        FUSO = 0
    except Exception as e:
        text_message = 'EXCEPT GET ACESSO FIREBASE LOGIN SENHA'
        quadroOperacao.add_card_list_name('ERRO PARA COLETAR DADOS DE ACESSO DO FIREBASE PARA BPM E FLUIG','erro','E-mails')
        data = {'atualizacao': datetime.now(), 'status': 'online', 'info': text_message}
        afb.update_collection('botsStatus', 'sistemaConstrutoras', data)
        return str(e)

    ### Homelend #####################################################
    LISTA_SISTEMAS = ['Bpm','Fluig', 'Homelend', 'Forcasa', 'Tenda']
    construtora = 'Homelend'
    try:
        if executarHomelend == 'SIM':
            print('---- HOMELEND ----')
            r = homelendReq.reqHomelend(homelendLogin, homelendSenha, sicaq_dict)
            print(r)
        else:
            data = {'atualizacao': datetime.now(), 'status': 'offline', 'info': MSG_ROBO_DESLIGADO.format(construtora)}
            afb.update_collection('botsStatus', construtora, data)
            time.sleep(3)
    except Exception as e:
        print(str(e))
        print('Exception sistemaConstrutoras - Homelend: ' + str(e))
        data = {'atualizacao': datetime.now(), 'status': 'except', 'info': "except: " + str(e)}
        afb.update_collection('botsStatus', construtora, data)
        time.sleep(3)
    print('---- FIM HOMELEND ----')

    ### FLUIG #####################################################
    try:
        construtora = 'Fluig'
        if executarFluig == 'SIM':
            r = fluig.mainloop(fluigsession, fluigLogin, fluigPassword, FUSO, quadroOperacao, sicaq_dict)
            print('----- RETORNO FLUIG MAIN -----')
            print(r)
            # criacao ocorre dentro da funcao fluig.mainloop()
            #r = criaCartao(r,'FLUIG|')
            print('----- RETORNO CRIA CARTAO FLUIG MAIN -----')
            print(r)
        else:
            data = {'atualizacao': datetime.now(), 'status': 'offline', 'info': MSG_ROBO_DESLIGADO.format(construtora)}
            afb.update_collection('botsStatus', construtora, data)
    except Exception as e:
        print('Exception sistemaConstrutoras - fluig: ' + str(e))
        data = {'atualizacao': datetime.now(), 'status': 'except', 'info': "excpt: " + str(e)}
        afb.update_collection('botsStatus', construtora, data)
        time.sleep(3)

    ##### FORCASA ##################################################
    # nome deve ser igual a colecao do firebase
    construtora = 'Forcasa'
    try:
        if executarForCasa == 'SIM':
            print('====== INICIO EXECUCAO FORCASA ======')
            sistForCasa.update_login_password(forCasaLogin, forCasaSenha)
            r, data = sistForCasa.get_data()
            print('----- RETORNO FORCASA get_data -----')
            print(r)
            r = criaCartaoForCasa(r, data, 'ForCasa', FUSO, sicaq_dict)
            print('----- RETORNO CRIA CARTAO ForCasa MAIN -----')
            print(r)
            data = {'atualizacao': datetime.now(), 'status': 'online', 'info': str(r)}
            afb.update_collection('botsStatus', construtora, data)
            print('====== FIM EXECUCAO FORCASA ======')
        else:
            data = {'atualizacao': datetime.now(), 'status': 'offline', 'info': MSG_ROBO_DESLIGADO.format(construtora)}
            afb.update_collection('botsStatus', construtora, data)
    except Exception as e:
        print(str(e))
        print('Exception sistemaConstrutoras - forcasa: ' + str(e))
        data = {'atualizacao': datetime.now(), 'status': 'except', 'info': str(e)}
        afb.update_collection('botsStatus', construtora, data)

    ##### BPM ##################################################
    construtora = 'Bpm'
    try:
        if executarBPM == 'SIM':
            bpm_session = requests.Session()
            dadosPropostas = bpm.main(bpmLogin, bpmPassword, bpm_session)
            print('----- RETORNO {} MAIN -----'.format(construtora))
            print(dadosPropostas)
            r = criaCartaoBpm(dadosPropostas,'BPM', FUSO, sicaq_dict)
            print('----- RETORNO CRIA CARTAO BPM MAIN -----')
            print(r)
            data = {'atualizacao': datetime.now(), 'status': 'online', 'info': str(r)}
            afb.update_collection('botsStatus', 'Bpm', data)
        else:
            data = {'atualizacao': datetime.now(), 'status': 'offline', 'info': MSG_ROBO_DESLIGADO.format(construtora)}
            afb.update_collection('botsStatus', 'Bpm', data)
            time.sleep(3)
    except Exception as e:
        print('Exception sistemaConstrutoras - bpm: ' + str(e))
        data = {'atualizacao': datetime.now(), 'status': 'except', 'info': str(e)}
        afb.update_collection('botsStatus', 'Bpm', data)

    ##### Tenda ##################################################
    # nome deve ser igual a colecao do firebase
    construtora = 'Tenda'
    try:
        if executarTenda == 'SIM':
            r = tenda.main(tendaLogin, tendaSenha, sicaq_dict)
            print('----- RETORNO {} MAIN -----'.format(construtora))
            # Atualizacao do firebase dentro da fc tenda.main
            print(r)
        else:
            data = {'atualizacao': datetime.now(), 'status': 'offline', 'info': MSG_ROBO_DESLIGADO.format(construtora)}
            afb.update_collection('botsStatus', construtora, data)
    except Exception as e:
        print('Exception sistemaConstrutoras - {}: {} '.format(construtora,e) )
        data = {'atualizacao': datetime.now(), 'status': 'except', 'info': str(e)}
        afb.update_collection('botsStatus', construtora, data)


######## === #########
def cria_cartao(r, data, construtora, FUSO, sicaq_dict):
    print('===== inicio cria cartao {} ======'.format(construtora))
    nomeCard = 'na'
    if str(r) == 'True':
        print('--- data got: ---')
        # print(data)
        print(len(data))
        if len(data) > 0:
            print('--- LEN DATA  > 0 ---')
            configDoc = afb.get_document_by_name_from_collection('configSistemaConstrutoras', construtora)
            nomeLista = configDoc.get('listaPastaNova', 'E-mails')
            prazoHoras = configDoc.get('prazoHoras', '2')
            pos = configDoc.get('prioridade', 'bottom')
            labels = configDoc.get('labels', '')
            print(data)
            print('item loop:')
            for item in data:
                nomeCard = item
                descr = ""
                naoExisteCartaoCriado, info = verificaSeExisteCartao(nomeCard)

                # procura no Firebase se nao encontrar no Trello e atualiza a variavel de acordo com o Firebase
                if naoExisteCartaoCriado:
                    pass
                    #naoExisteCartaoCriado = procuraFirebase(nomeCard)

                descr = descr + str(info)
                print("nomeCard: {}".format(nomeCard))
                print('naoExisteCartaoCriado: ' + str(naoExisteCartaoCriado))
                if naoExisteCartaoCriado:
                    r = portalApp.verificaELoga()
                    if r == 'LOGADO':
                        cpf = item.split("|")
                        cpf = cpf[-1]
                        cpf = cpf.strip()
                        cpf = cpf.replace(".", "")
                        cpf = cpf.replace("-", "")
                        cpf = cpf[-11:]
                        print(cpf)
                        numContratos, primeiroContrato, etapaPortal = portalApp.get_info_cpf(cpf)
                        descr = descr + " " + etapaPortal
                    else:
                        print('**** ERRO NO LOGIN DO PORTAL *****')
                    print(' For Casa item: naoExisteCartaoCriado: {}'.format( str(naoExisteCartaoCriado)))
                    rCria, cardid = criaCartaoComValidacao(construtora, nomeCard,descr,nomeLista,prazoHoras,pos,labels, FUSO)
                    print(rCria)
                    if rCria == 'ok':
                        print('==== Cartao criado com sucesso! ====')
                        #quadroOperacao.add_checklist_by_id(cardid, checkListidPadraoAnaliseModelo)
                    else:
                        print('*** ERRO: ' + str(rCria))
                else:
                    print(f'Ja existe cartao no quadro: {nomeCard}')
                    print('========================================')

        else:
            print('--- LEN DATA = 0 , NOTHING TO ADD---')
    else:
        print('************ ERRO {} ********************'.construtora)
        nomeCard = 'ERRO DE LOGIN NO SCRIPT '
        naoExisteCartaoCriado, info = verificaSeExisteCartao(nomeCard)
        descr = 'logar novamente ' + str(info)
        if naoExisteCartaoCriado:
            cardid, rstatus = quadroOperacao.add_card_list_name(nomeCard, descr, 'E-mails', '2', FUSO)
            printMessage = '*** CARTO ERRO CRIADO'
            print(printMessage + "|" + cardid + "|" + rstatus)
        else:
            print('***** ERRO  - JA EXISTE CARTAO DE AVSIO NO TRELLO *****')

    return nomeCard
#########

def criaCartaoForCasa(r, data, construtora, FUSO, sicaq_dict):
    print('===== inicio cria cartao ForCasa ======')
    nomeCard = 'na'
    if str(r) == 'True':
        print('--- data got: ---')
        # print(data)
        print(len(data))
        if len(data) > 0:
            print('--- LEN DATA  > 0 ---')
            configDoc = afb.get_document_by_name_from_collection('configSistemaConstrutoras', 'forCasa')
            nomeLista = configDoc.get('listaPastaNova', 'E-mails')
            prazoHoras = configDoc.get('prazoHoras', '2')
            pos = configDoc.get('prioridade', 'bottom')
            labels = configDoc.get('labels', '')
            print(data)
            print('item loop:')
            for item in data:
                nomeCard = 'ForCasa' +" "+ str(item.get('cod','na')) +" " \
                        +" "+ item.get('empreendimento','na') +" "+ item.get('cliente','na') +" " + item.get('cpf','na')
                descr = item.get('dataCadastro','na') #+ " " + item.get('fase','na')
                naoExisteCartaoCriado, info = verificaSeExisteCartao(nomeCard)

                # procura no Firebase se nao encontrar no Trello e atualiza a variavel de acordo com o Firebase
                if naoExisteCartaoCriado:
                    pass
                    #naoExisteCartaoCriado = procuraFirebase(nomeCard)

                descr = descr + str(info)
                print("nomeCard: {}".format(nomeCard))
                print('naoExisteCartaoCriado: ' + str(naoExisteCartaoCriado))
                if naoExisteCartaoCriado:
                    cpf = item.get('cpf')
                    cpf = cpf.replace(".", "")
                    cpf = cpf.replace("-", "")
                    r = portalApp.verificaELoga()
                    if r == 'LOGADO':
                        numContratos, primeiroContrato, etapaPortal = portalApp.get_info_cpf(cpf)
                        descr = descr + " " + etapaPortal
                    else:
                        print('**** ERRO NO LOGIN DO PORTAL *****')
                    print(' For Casa item: naoExisteCartaoCriado: {}'.format( str(naoExisteCartaoCriado)))

                    # pesquisa no SICAQ
                    if cpf != '':
                        descr = sicaq.pesquisa_sicaq(sicaq_dict, 'sistemaConstrutoras'+construtora, cpf, descr)

                    # Cria cartao
                    rCria, cardid = criaCartaoComValidacao(construtora, nomeCard,descr,nomeLista,prazoHoras,pos,labels, FUSO)

                    print(rCria)
                    if rCria == 'ok':
                        print('==== Cartao criado com sucesso! ====')
                        #quadroOperacao.add_checklist_by_id(cardid, checkListidPadraoAnaliseModelo)
                    else:
                        print('*** ERRO: ' + str(rCria))
                else:
                    print(f'Ja existe cartao no quadro: {nomeCard}')
                    print('========================================')

        else:
            print('--- LEN DATA = 0 , NOTHING TO ADD---')
    else:
        print('************ ERRO NO FOR CASA ********************')
        nomeCard = 'ERRO DE LOGIN NO SCRIPT FORCASA'
        naoExisteCartaoCriado, info = verificaSeExisteCartao(nomeCard)
        descr = 'logar novamente ' + str(info)
        if naoExisteCartaoCriado:
            cardid, rstatus = quadroOperacao.add_card_list_name(nomeCard, descr, 'E-mails', '2', FUSO)
            printMessage = '*** CARTO ERRO FORCASA CRIADO'
            print(printMessage + "|" + cardid + "|" + rstatus)
        else:
            print('***** ERRO FOR CASA- JA EXISTE CARTAO DE AVSIO NO TRELLO *****')
    return nomeCard


def procuraFirebase(nomeCard):
    list_documents = afb.query_collection('trellowebhook', 'name', nomeCard)
    if len(list_documents) == 0:
        print('cartao NAO existe no firebase, criar o cartao: {}'.format(nomeCard))
        naoExisteCartaoCriado = True
    elif len(list_documents) == 1:
        print('cartao EXISTE no firebase, NAO criar o cartao: {}'.format(nomeCard))
        # se achar no Firebase, seta a variavel para False, independente do valor anterior
        naoExisteCartaoCriado = False
    else:
        x9('mais de um cartao encontrado no firebase: '+ nomeCard +str(len(list_documents)))
        naoExisteCartaoCriado = False
    return naoExisteCartaoCriado

def criaCartaoComValidacao(construtora, nomeCard,descr,nomeLista,prazoHoras,pos,labels, FUSO):
    r = ''
    # funcao para reduzir tamanho do codigo com partes repetidas
    cardid, rstatus = quadroOperacao.add_card_list_name(nomeCard, descr, nomeLista, prazoHoras, pos, labels, FUSO)

    anomesdia = datetime.now().strftime("%Y%m%d")
    datetimenow = str(datetime.now())  # .strftime("%Y%m%d_%H%M%S")
    data = {'name':nomeCard,'construtora':construtora,'datetime':datetimenow,'anomesdia':anomesdia,'cardid':cardid}
    #afb.save_info_firestore('sistConstCartoes' + anomesdia, cardid, data)
    if rstatus == 200:
        print(construtora + ' cardid' + str(cardid))
        resp = afb.save_info_firestore('trellowebhook', cardid, data)
        print('NOVO CARTAO CRIADO: ' + str(cardid) + "|" + str(rstatus) + "|" + str(nomeCard))
    else:
        # segunda tentativa com texto simples
        cardid, rstatus = quadroOperacao.add_card_list_name(nomeCard, 'erro na criacao do cartao', 'E-mails', '2')
        if rstatus == 200:
            print(construtora + ' cardid' + str(cardid) + "|" + str(rstatus))
            resp = afb.save_info_firestore('trellowebhook', cardid, data)
            r = 'erro 1'
        else:
            print('Erro ao criar CARTAO para: '+ construtora + " " + str(cardid))
            cardid, rstatus = quadroOperacao.add_card_list_name('ERRO SCRIPT CONSTRUTORA', 'erro na criacao', 'E-mails', '2')
            printMessage = 'ERRO SCRIPT construtoras'
            print(printMessage + "|" + str(cardid) + "|" + str(rstatus))
            x9('ERRO SCRIPT CONSTRUTORA: ' + str(cardid))
            x9(nomeCard)
            r = 'erro 2'
    return r, cardid


def criaCartaoBpm(r,construtora, FUSO, sicaq_dict,list_card='Email-s'):
    print('Inicio criaCartao')
    nomeCard = "na"
    # bpm retorna list de lists, cada list refere-se a uma proposta com [descr, cpf, horaRecebida, str(pac)] cada
    criarCartao = True
    #printMessage = 'nenhum cartao para criar'
    print(r)
    if r[0][0] == 'NAO LOGADO':
        verifica_cria_cartao(construtora)
    else:
        configDoc = afb.get_document_by_name_from_collection('configSistemaConstrutoras', 'bpm')
        print('EM ELSE CRIA CARTAO BPM')
        ii = 0
        for item in r:
            # FORMATO item: [pac,cpf,descr,recebido,situacao]
            print(item)
            time.sleep(1)
            consulta_portal = False
            if item[0] == 'na':
                criarCartao = False
                # nao cria cartao pq nao tem proposta qdo resposta eh 'na'
                print('em if item[0] == na')
            else:
                print('else nomeCard = item[0]')
                if item[0] == 'mais de 10 propostas':
                    # item que avisa sobre a existencia de mais de 10 propostas, alguem precisa olhar o BPM
                    descr = 'mais de 10 propostas no BPM'
                    nomeCard = 'BPM com mais de 10 propostas'
                    cpf = ''
                    consulta_portal = False
                else:
                    # e um item de uma proposta no FORMATO [pac,cpf,descr,recebido,situacao]
                    # nome = descricao + PAC .
                    nomeCard = str(item[2]) + "| PAC: " + str(item[0])
                    descr = construtora + ' | cpf: ' + item[1] + "| hora recebido: " +item[3] + "| status: " + item[4]

                    cpf = item[1]
                    cpf = cpf.replace(".", "")
                    cpf = cpf.replace("-", "")

                    if str(cpf).isdigit():
                        descr = sicaq.pesquisa_sicaq(sicaq_dict, 'sistemaConstrutoras' + construtora, cpf, descr)
                        print(descr)

                        consulta_portal = True

                print('chama verificaSeExisteCartao(nomeCard)')
                naoExisteCartaoCriado, info = verificaSeExisteCartao(nomeCard)
                # procura no Firebase se nao encontrar no Trello e atualiza a variavel de acordo com o Firebase
                if naoExisteCartaoCriado:
                    pass
                    #naoExisteCartaoCriado = procuraFirebase(nomeCard)

                descr = descr + info
                print('criarCartao e naoExisteCartaoCriado: {},{}'.format(str(criarCartao),str(naoExisteCartaoCriado)))
                time.sleep(1)
                if criarCartao and naoExisteCartaoCriado:
                    nomeLista = configDoc.get('listaPastaNova', 'E-mails')
                    prazoHoras = configDoc.get('prazoHoras', '2')
                    pos = configDoc.get('prioridade', 'bottom')
                    labels = configDoc.get('labels', '')

                    if consulta_portal:
                        # consulta portal
                        r = portalApp.verificaELoga()
                        if r == 'LOGADO':
                            numContratos, primeiroContrato, etapaPortal = portalApp.get_info_cpf(cpf)
                            descr = descr + " " + etapaPortal + " " + str(cpf)
                        else:
                            print('*** ERRO NO LOGIN DO PORTAL ***')
                            x9('ERRO NO LOGIN DO PORTAL - SCRIPT CONSTRUTORA {}'.format(construtora))

                    if cpf != '':
                        # pesquisa SICAQ pode tirar ponto e traco do cpf
                        descr = sicaq.pesquisa_sicaq(sicaq_dict, 'sistemaConstrutoras'+construtora, cpf, descr)

                    print('DESCRICAO CARTAO BPM: ' + descr)
                    cardid,rstatus=quadroOperacao.add_card_list_name(nomeCard,descr,nomeLista,prazoHoras,pos,labels,FUSO)
                    anomesdia = datetime.now().strftime("%Y%m%d")
                    datetimenow = str(datetime.now())  # .strftime("%Y%m%d_%H%M%S")
                    data = {'name':nomeCard,'construtora':construtora,'datetime':datetimenow,'anomesdia':anomesdia,'cardid':cardid}
                    #afb.save_info_firestore('sistemaConstrutorasCartoesCriados' + anomesdia, cardid, data)
                    if rstatus == 200:
                        url = PAC_MRV_PNG
                        r = quadroOperacao.add_attachment(cardid, url)
                        printMessage = 'NOVO CARTAO CRIADO: '
                        print(printMessage + "|" + str(cardid) + "|" + str(rstatus) + "|" + str(nomeCard))
                        resp = afb.save_info_firestore('trellowebhook', cardid, data)
                        print('BPM cardid' + str(cardid))
                    else:
                        # segunda tentativa com texto simples
                        cardid, rstatus = quadroOperacao.add_card_list_name(nomeCard, 'erro na criacao do cartao', 'E-mails', '2')
                        if rstatus == 200:
                            url = PAC_MRV_PNG
                            r = quadroOperacao.add_attachment(cardid, url)
                            print('BPM cardid' + str(cardid)+ "|" + str(rstatus))
                            resp = afb.save_info_firestore('trellowebhook', cardid, data)
                        else:
                            print('Erro ao criar CARTAO para BPM: ' + str(cardid))
                            cardid,rstatus=quadroOperacao.add_card_list_name('ERRO SCRIPT BPM','erro na criacao','E-mails','2')
                            printMessage = 'ERRO SCRIPT BPM'
                            print(printMessage + "|" + str(cardid) + "|" + str(rstatus))
                            x9('ERRO SCRIPT BPM: ' + str(cardid))
                            x9(nomeCard)
                else:
                    print('---cartao para proposta BPM ja existe no quadro ----')
                    print(nomeCard)
                    print('----------------------------------------------------')

    return nomeCard

def verifica_cria_cartao(construtora):
    printMessage = 'logar novamente'
    nomeCard = '{} | LOGAR NOVAMENTE'.format(construtora)
    naoExisteCartaoCriado, info = verificaSeExisteCartao(nomeCard)
    descr = 'logar novamente ' + str(info)
    if naoExisteCartaoCriado:
        cardid, rstatus = quadroOperacao.add_card_list_name(nomeCard, descr, list_card, '2')
        if str(rstatus) != '200':
            print('rstatus: ' + str(rstatus))
            # NAO PRECISA CRIAR ESSE CARTAO NO FIREBASE
        print(printMessage + "|" + cardid + "|" + rstatus)
    return 'ok'

def verificaSeExisteCartao(nome, excluirLista='Finalizados'):
    ''':nome e o nome do cartao
    retorna mensagem de erro do trello. Se for sucesso, retorna 'ok'
    '''
    searchString = '"'+ nome + '"' + " is:open -list:Finalizados"
    print('==== VERIFICANDO EXISTENCIA DE CARTAO, searchString: ====')
    print(searchString)
    print("=========================================================")
    cardDict = quadroOperacao.search_board_cards(searchString)
    print(cardDict)
    time.sleep(1)
    info = ''
    if len(cardDict) == 0:
        print('nao encontrou cartao no trello - BPM')
        criaCartao = True
        # print(nomeCard)
    elif cardDict[0].get('id') == 'na':
        print('ERRO NA BUSCA sem info sobre cartao no trello: ' + nome)
        criaCartao = True
        info = ' ERRO NA BUSCA DO TRELLO. CODIGO DE ERRO: '+ str(cardDict[0].get('desc'))
    else:
        print('cartao esta no trello, verificar se esta closed (arquivado) ou na lista finalizados:')
        # cardid = cardDict[0].get('id')
        resp = verificaCartaoSearchTrello(cardDict)
        criaCartao = True
        if resp:
            print('cartao esta no quadro - nao esta arquivado e nem na lista Finalizados')
            print('nao precisa criar outro cartao:   ' + nome)
            print('================= NAO CRIAR CARTAO, VERIFICAR PROXIMO CARTAO DO DICT =====================')
            print(" ")
            criaCartao = False
    return criaCartao, info


def verificaCartaoSearchTrello(cardDict):
    print('--- verifica Cartao Search Trello ---')
    resp = False
    #procura um cartao aberto e fora da lista finalizados no quadro:
    for card in cardDict:
        cardjson = quadroOperacao.get_card_by_id(card.get('id'))
        #print(card.get('name'))
        print(cardjson.get('name'))
        time.sleep(3)
        # verifica se o cartao esta arquivado no quadro, se a lista nao eh a finalizados e se o nome eh igual
        if cardjson.get('closed') == False and cardjson.get('idList','') != LISTFINALIZADOSBOARDOPERACAO and \
            card.get('name') in cardjson.get('name'):
            print('==== cartao valido no quadro, nao criar ====')
            resp = True
            break
    return resp

if __name__=='__main__':
    while True:
        r = main() #pesquisaFluig()

