import signal, random
import keyboard
from multiprocessing import Process, Array
from threading import Semaphore, Lock
import time
import sysv_ipc

#Shared Memory 
MessQueue= sysv_ipc.MessageQueue(42)        #C'est par cette queue que vont se réaliser tout les échanges entre chaque joueur. Vu que les actions sont bloqué par le sempaohr du signal il ne peut pas y avoit plusieurs echange en meme temps donc pas besoin de plusieurs queue
LockEchange = Lock()
semSignal = Semaphore(0) #va empecher qu'un autre joueur clique sur un signal alors qu'un joueur est en train de faire une action apres avoir fait un signal
#Array offre et echange sont déclarer dans le main mais accessible de partout

def distribCartes(nbJoueurs): 
    typeCartesJeu = ["Montgolfière", "Camion", "Snowboard", "Trotinette", "Deltaplane"] #cartes disponibles dans le jeu, chacune en 5 exemplaires
    ensembleDeck = [ [0 for i in range(5)] for _ in range(nbJoueurs) ] #il y a autant de deck que de joueurs et chaque deck contient 5 cartes
    typeCartePartie = [] #va contenir les types de carte qu'on utilise pour la partie, il y a autant de types que de nombre de joueurs
    
    #on choisit avec quels types de cartes on va jouer durant la partie
    for i in range(nbJoueurs):
        x = typeCartesJeu[random.randint(0,len(typeCartesJeu)-1)] #on tire un type de cartes au hasard dans le jeu
        typeCartePartie.append(x) #on inclut ce type dans notre partie
        typeCartesJeu.remove(x)   #on le supprime de la liste du jeu pour ne pas avoir de doublons
    
    #on veut définir l'ensemble des cartes de la partie, il y a 5 cartes de chaque type
    ensemblePartie = []
    for i in range(len(typeCartePartie)):
        tab = [typeCartePartie[i]]*5
        ensembleJeu = ensembleJeu + tab
    
    #on distribue aléatoirement 5 cartes aux joueurs
    for i in range(nbJoueurs):
        for j in range(0,5):
            carte = ensembleJeu[random.randint(0,len(ensembleJeu)-1)]
            ensembleDeck[i][j] = carte
            ensembleJeu.remove(carte)
      
    return ensembleDeck


def handler():
    global tabEchange
    while True:
        semSignal.acquire()
        if keyboard.read_key == "j": #le joueur appuie sur la touche j car il veut faire quelquechose (j car à peu pres au milieu du clavier)
            qui=input("qui veut faire une action?")
            quoi=input("quelle action veux-tu faire ? Si tu veux faire une offre entre O, si tu veux accepter une offre, entre A")
            if quoi=="O":
                combien=input("Combien de cartes proposes-tu ?")
                echange[int("qui")] = combien
            if quoi=="A":
                num_offre=input("L'offre de quel joueur veux-tu accepter ? Entre le numero du joueur associe.")
                # on indique dans le tabEchange que "qui" et "num_offre" veulent échanger
                echange[qui]=1 #celui qui accepte l'offre
                echange[num_offre]=2 #celui qui avait fait l'offre
                while echange[qui] != 0 or echange[num_offre] !=0 : #permet d'avoir le temps de faire les échanges de cartes entre les deux joueurs
                    pass
                #echangerCartes(qui,num_offre) #demander quelles cartes "qui" souhaite echanger puis realiser l'echange entre qui et le joueur de l'offre
        if keyboard.read_key == "n": #Le joueur a 5 cartes identiques, il appuie sur la "cloche"
            gagnant=input("qui a sonne la cloche ?")
            print(gagnant)
            break
    semSignal.release()


def player(id,deck):        #Not sure mais peut etre mettre globale messqueue et Lock echange mais pas sur sur 
    while 1==1:

        if echange[id]== 1 or echange[id] == 2:      #On est dans la parti d'échange 1 : qui accepte l'offre, 2 : qui a fait l'offre
            found= False
            i=1
            while found == False :
                if i == id:
                    i=i+1
                if echange[i]!= 0:
                    found = True

            if LockEchange.locked() == False:             #Le sémaphore a été pris par l'autre joueur du coup ce joueur la se met en reception
                message, t = MessQueue.recieve()
                message = message.decode()
                cartes_reçu= message.split(";")
                deck.append(cartes_reçu)
                

            LockEchange.acquire()
            #   Dans cette partie on va regarder qui a fait l'offre accepté pour connaitre le nombre de carte a échanger et suppr les carte de son jeu      

            if echange[id]==2:      ##Si on est le joueur dont l'offre est accepté
                nbCarte = offre[id]
                
            else :                  #On est pas le joueur dont l'offre est accepté
                nbCarte = offre[i]

            typeCarte = input("Quel est le type de la ou des carte(s) que vous voulez donné (avion, train, etc) ? : ")
            for j in range(nbCarte):
                deck.remove(typeCarte)      #Ptetre ici regarder si toute lees cartes sont dans le deck
                txt = txt+typeCarte
                if j != nbCarte-1:
                    txt=txt+";"

            
            MessQueue.send(txt.encode())
            echange[id]=0
            LockEchange.release()
           
        fich= "joueur"+str(id)+".txt"
        with open(fich, "w") as fichier:
            fichier.write("Bonjour player "+str(id))
            fichier.write("\nVos cartes sont les suivantes : ")
            for i in range(len(deck)):
                fichier.write(deck[i]+" ")
            fichier.write("\nLes dernières annonces sont : ")
            for j in range(len(offre)):
                fichier.write("Joueur "+str(j)+" : "+str(offre[j])+" carte(s)")
                
        
def game(nbJoueurs):
    decks = distribCartes(nbJoueurs)
    players = [ Process(target = player, args = (i, decks[i],)) for i in range(nbJoueurs) ]
    handler() 


if __name__ == "main":
    jouer = 0

    while jouer == 0:
        nbJoueurs=0
        while (nbJoueurs > 6) and (nbJoueurs < 3) :
            nbJoueurs = int(input("Combien de joueurs vont jouer ?")) 
        offre = Array('i', range(nbJoueurs), Lock= True)
        echange = Array('i', range(nbJoueurs))
        partie = Process(target = game, args = (nbJoueurs,))
        partie.start()
        partie.join()
        jouer = input("Voulez-vous rejouer ? Entrer 0 pour oui ou 1 pour non")


