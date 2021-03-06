from concurrent.futures import thread
import signal, random, sysv_ipc
import keyboard
import os
from multiprocessing import Process, Array
from threading import Semaphore, Lock
import time

#Shared Memory
rien = 0
accept = 1
offrant = 2
fini= 3
gagne = 4

endOfGame=False

key = 42
MessQueue= sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)      
#C'est par cette queue que vont se réaliser tout les échanges entre chaque joueur. Vu que les actions sont bloqué par le sempaohr du signal il ne peut pas y avoit plusieurs echange en meme temps donc pas besoin de plusieurs queue
LockEchange = Lock()
lockSignal = Lock() #va empecher qu'un autre joueur clique sur un signal alors qu'un joueur est en train de faire une action apres avoir fait un signal
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
    ensembleJeu = []
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


def handler(sig,frame):
    global tabEchange,endOfGame, rien, fini, offrant, accept
    print("on est dans le handler")
    if sig == signal.SIGUSR1 :  #un joueur souhaite faire une action, après avoir faire kill -SIGUSR1 pidGame dans un autre terminal 
        lockSignal.acquire()    #on utilise un lock pour que les autres joueurs ne puissent pas envoyer de signau en même temps
        try :
            qui=input("Quel joueur souhaite faire une action ? ")
        except EOFError:
            print("erreur")
            qui = 1
        #quoi=input("quelle action veux-tu faire ? Si tu veux faire une offre entre O, si tu veux accepter une offre, entre A")
        quoi = "O"
        
        if quoi=="O":
            #combien=int(input("Combien de cartes proposes-tu ?"))
            combien = 1
            offre[qui] = combien
            print("Apres offre")
        quoi = "A"
        if quoi == "A":
            try :
                num_offre=input("L'offre de quel joueur veux-tu accepter ? Entre le numero du joueur associe.")
            
            except  EOFError :
                print("erreur")
                num_offre=1

            # on indique dans le tabEchange que "qui" et "num_offre" veulent échanger
            qui=0
            echange[qui]=accept #celui qui accepte l'offre
            echange[num_offre]= offrant#celui qui avait fait l'offre
            while echange[qui] != fini or echange[num_offre] != fini: #permet d'avoir le temps de faire les échanges de cartes entre les deux joueurs
                pass
            time.sleep(1)
            echange[qui]=rien  #celui qui accepte l'offre
            echange[num_offre]=rien #celui qui avait fait l'offre
            print("On a remis a 0")
            offre[num_offre]=0
        lockSignal.release()
       
    

    if sig == signal.SIGUSR2:
        lockSignal.acquire()
        print("ok")
        
        #gagnant=input("qui a sonne la cloche ?")
        gagnant = 0
        #echange[gagnant]= gagne
        print(gagnant)
        endOfGame=True
        lockSignal.release()


def player(id,deck,echange, offre):        #Not sure mais peut etre mettre globale messqueue et Lock echange mais pas sur sur
    global endOfGame, rien, fini, offrant, accept
    while endOfGame != True:

        
        if echange[id] == offrant or echange[id]== accept:      #On est dans la parti d'échange, 1 : qui accepte l'offre, 2 : qui a fait l'offre
            print("joueur ", id, deck)
            print(id, "Participe à un échange")
            found= False
            autreJoueur=0                           #correspond au joueur avec qui on va faire l'échange

            while found == False :                  #On cherche avec qui on échange
                if autreJoueur == id :
                    autreJoueur=autreJoueur+1
                if echange[autreJoueur]!= 0:
                    found = True
                else:
                    autreJoueur += 1
            print("Avec le joueur ", autreJoueur)
            
            if echange[id]== offrant:      ##Si on est le joueur dont l'offre est accepté
                nbCarte = offre[id]
                    
            else :                  #On est pas le joueur dont l'offre est accepté
                nbCarte = offre[autreJoueur]
            
            print("On doit echanger ", nbCarte, " Cartes")
           
            while(echange[id] != fini or echange[autreJoueur]!= fini):
                if echange[autreJoueur]!= fini:
                    if LockEchange.locked() == True:          #Si le lock est pris et que l'autre joueur n'a pas 
                        print("Le joueur ", id ," n'a pas pris le lock et va donc recevoir")
                        message, t = MessQueue.receive()
                        message = message.decode()
                        for i in range(nbCarte):
                            deck.append(message)
                        print(id, " a recu des cartes de ", autreJoueur, message)
                        print(deck)
                    

                if echange[id]!=fini :
                    LockEchange.acquire()
                    print("Le joueur ", id, " a pris le lock et va faire son echange")
                #   Dans cette partie on va regarder qui a fait l'offre accepté pour connaitre le nombre de carte a échanger et suppr les carte de son jeu      

                    print("Le player ", id, " va donner ses cartes au joueur ", autreJoueur)
                    posCarte= 0 #input("Donnez la position d'une carte du type que vous souhaitez échanger : ")
                    typeCarte = deck[posCarte]
                    print(typeCarte)
                    for j in range(nbCarte):
                        deck.remove(typeCarte)     #Ptetre ici regarder si toute lees cartes sont dans le deck

                    print(id, " a envoyé des cartes a ", autreJoueur)
                    MessQueue.send(typeCarte.encode())
                    print(id, "On a bien envoyé ")
                    echange[id]=fini
                    print(id, "On a bien envoyé et update echange", echange[id])
                    
                    LockEchange.release()

            print("joueur ", id, deck)

            if echange[id]==gagne:
                carte = deck[0]
                for i in range(len(deck)):
                    if deck[i]!=carte:
                        erreur = True
                        break
                erreur = False
                if erreur == False :
                    print("vous avez gagné !")
                    endOfGame=True




        
        fich= "joueur"+str(id)+".txt"
        with open(fich, "w") as fichier:
            fichier.write("Bonjour player "+str(id))
            fichier.write("\nVos cartes sont les suivantes : ")
            for i in range(len(deck)):
                fichier.write(deck[i]+" ")
            fichier.write("\nLes dernières annonces sont : ")
            for j in range(len(offre)):
                fichier.write("Joueur "+str(j)+" : "+str(offre[j])+" carte(s)")
                
        
def game(nbJoueurs, echange, offre):
    decks = distribCartes(nbJoueurs)
    print(os.getpid())
    print(decks)
    players = [ Process(target = player, args = (i, decks[i], echange, offre,)) for i in range(nbJoueurs) ]
    for i in players :
        i.start()
    print("On a lancé les playe1s")
    signal.signal(signal.SIGUSR1, handler)
    for i in players:
        i.join()
    for i in players:
        i.close()

    print("tout les players se sont arreté")

if __name__ == "__main__":
    jouer = 0
    while jouer == 0:
        nbJoueurs=0
        nbJoueurs = 3 #int(input("Combien de joueurs vont jouer ?"))
        offre = Array('i', range(nbJoueurs))
        echange = Array('i', range(nbJoueurs))
        for i in range(nbJoueurs):
            echange[i]=0
            offre[i]=0
        partie = Process(target = game, args = (nbJoueurs,echange,offre,))
        partie.start()
        #signal.signal(signal.SIG, handler)
        partie.join()
        partie.close()
        print("La partie s'arrete")
        jouer = int(input("Voulez-vous rejouer ? Entrer 0 pour oui ou 1 pour non"))
        print(jouer)