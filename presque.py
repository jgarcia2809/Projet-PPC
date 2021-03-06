from concurrent.futures import thread
import signal, random, keyboard
from tokenize import String
import os
from multiprocessing import Process, Array, Queue, Lock
from threading import Semaphore
import time

#Shared Memory
rien = 0
accept = 1
offrant = 2
fini= 3
gagne = 4
chgOffre = 5

endOfGame=False


MessQueue= Queue() #c'est la queue qui va nous permettre d'échanger les cartes entre deux joueurs
askQueue = Queue() #c'est la queue qui va nous permettre d'intéragir avec l'utilisateur 
LockEnvoie = Lock() #Lock que va prendre le joueur quand il doit envoyer ses cartes
lockRecept= Lock()  #Lock que va prendre le joueur quand il doit recevoir des cartes
lockSignal = Lock() #va empecher qu'un autre joueur clique sur un signal alors qu'un joueur est en train de faire une action apres avoir fait un signal

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


def handler1(sig,frame):
    
    print("on est dans le handler1")
    if sig == signal.SIGUSR1 :  #un joueur souhaite faire une action, il l'indique en faisant kill -SIGUSR1 pidGame dans un autre terminal 
        lockSignal.acquire()    #on utilise un lock pour que les autres joueurs ne puissent pas envoyer de signal en même temps
        askQueue.put(1)  #on veut intéragit avec l'utilisateur, les input doivent être fait dans game
        while qui == -1 or quoi == "":
            print(qui, quoi)
            qui = askQueue.get()  #on réccupère le résultat du input fait dans game
            print(qui, quoi)
            quoi = askQueue.get()
            
        print("apres le qui quoi")
        if quoi=="o": #le joueur veut faire une offre

            askQueue.put(2)  #input pour savoir combien de carte on doit échanger
            while combien == 0:
                combien = askQueue.get()
            offre[qui] = combien  #on actualise le tableau des offres
            for i in range(len(echange)):
                echange[i] = chgOffre
            time.sleep(0.5)
            for i in range(len(echange)):
                echange[i] = rien

         
        if quoi == "a": #le joueur veut accepter une offre
           
            askQueue.put(3) #input pour savoir de qui il veut accepter l'offre
            while num_offre == -1:
                num_offre= askQueue.get()

            echange[qui]=accept 
            echange[num_offre]= offrant

            while echange[qui] != fini or echange[num_offre] != fini: #permet d'avoir le temps de faire les échanges de cartes entre les deux joueurs
                pass
            time.sleep(1)

            echange[qui]=rien  
            echange[num_offre]=rien 
            offre[num_offre]=0

    lockSignal.release()  #permet à un autre joueur de faire une action
    print(" Fin de l'action")
    #réinitialisation des inputs
    qui, quoi, combien, num_offre = -1,"", 0, -1
       
    
      #un joueur souhaite dire qu'il a gagné, il l'indique en faisant kill -SIGUSR2 pidGame dans un autre terminal 
       

def handler2(sig,frame):
    global endOfGame
    print("on est dasn le hanlder2")
    print("dans le sig2")
    lockSignal.acquire()
    print("dans le sig2")
    gagnant = -1
    askQueue.put(5)  #input pour savoir qui a gagné
    while (gagnant == -1):
        gagnant = askQueue.get() 
        print("Le gagnant est ", gagnant)
    echange[gagnant]= gagne
    print("gagne",gagne)
    print("echange du gagnant", echange[gagnant])
    print("on a update le tab echange")
    lockSignal.release()

def player(id,deck,echange, offre):        #Not sure mais peut etre mettre globale messqueue et Lock echange mais pas sur sur
    global endOfGame

    actualisation(id, deck)      #On va ecrire dans le fichier du joueur ses cartes du début
    print("gagne player",gagne)

    while endOfGame != True:

        if echange[id] == chgOffre :
            actualisation(id, deck)
        
        if echange[id]==gagne:   #permet le joueur qui se dit "gagnant" a vraiment gagné
            print(id, "j ai compris que je dois voir si jai gagné")
            actualisation(id, deck)
            carte = deck[0]
            erreur = False
            for i in range(len(deck)):
                if deck[i]!=carte:
                    erreur = True
                    print("Vous n'avez pas gagné, le jeu reprend")
                    echange[id]=-1
                    break
            if erreur == False :
                print("vous avez gagné !")
                endOfGame=True
        
            
        if echange[id] == offrant or echange[id]== accept:      #si le joueur est pris dans un échange (en tant que offrant ou accepatant)
            #le joueur doit trouver avec qui il fait son échange
            found= False         
            autreJoueur=0        #correspond au joueur avec qui on va faire l'échange

            while found == False :           #On cherche avec qui on échange
                if autreJoueur == id :
                    autreJoueur=autreJoueur+1
                if echange[autreJoueur]!= 0:
                    found = True
                else:
                    autreJoueur += 1
                    print(autreJoueur)
            
            #on réccupère le nombre de cartes qu'il faut échanger
            if echange[id]== offrant:      #Si on est le joueur dont l'offre est accepté
                nbCarte = offre[id]          
            else :                  #On on n'est pas le joueur dont l'offre est accepté
                nbCarte = offre[autreJoueur]
            
            recu= False
            envoie = False
            while(recu != True or envoie != True): 
                if recu == False :
                    lockRecept.acquire()   #le joueur se met en état de réception, l'autre joueur ne peut pas l'être
                    
                    stateLock = LockEnvoie.acquire()
                    if(MessQueue.empty() != True or stateLock == False ):  #si l'autre n'a pas encore envoyé, cela sert à rien de chercher un message
                        
                        message= MessQueue.get()
                        for i in range(nbCarte):
                            deck.append(message)  #on ajoute la carte au deck du joueur
                        recu = True
                    LockEnvoie.release()
                    lockRecept.release()
                

                if envoie == False :
                    LockEnvoie.acquire()  #le joueur se met en état d'envoi, l'autre ne peut pas l'être
        
                    #le joueur indique la position du type de carte à envoyer via un input
                    print("joueur", id, "à toi : ")
                    askQueue.put(4)  
                    
                    while posCarte == -1:
                        posCarte = askQueue.get()
                        print(posCarte)
                    
                    #le type des cartes à échanger est défini par la position de la carte
                    typeCarte = deck[posCarte]
                    for j in range(nbCarte):
                        deck.remove(typeCarte)     #on supprime les cartes à envoyer du deck du joueur
                        
                    MessQueue.put(typeCarte)
                    echange[id]=fini    #état du joueur = fini d'envoyé
                    envoie = True
                    time.sleep(0.5)
                    LockEnvoie.release()  
                actualisation(id, deck)

            posCarte = -1 #réinitialisation
            
           
        
        #écriture des decks des joueurs dans un fichier texte

def actualisation(id, deck):
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
    decks = distribCartes(nbJoueurs)  #on distribue un deck à chaque joueur
    print("PID : ", os.getpid())  #il faut le PID pour envoyer les signaux pour faire des actions
    players = [ Process(target = player, args = (i, decks[i], echange, offre,)) for i in range(nbJoueurs) ]  #on crée un process player pour chaque joueur
    for i in players :
        i.start()
    print("On a lancé les players")
    signal.signal(signal.SIGUSR1, handler1)
    signal.signal(signal.SIGUSR2, handler2)
    for i in players:
        i.join()
    for i in players:
        i.close()

    print("tout les players se sont arreté")

if __name__ == "__main__":
    jouer = 0
    while jouer == 0:
        nbJoueurs = 3 #int(input("Combien de joueurs vont jouer ?"))
        offre = Array('i', range(nbJoueurs))     #chaque case de offre correspond à un joueur, la valeur de la case associée correspond aux nombres de cartes que le joueur souhaite échanger
       
        echange = Array('i', range(nbJoueurs))  #chaque casee de echange correspond à un joueur et contient son état pendant un échange

        #€xplication rapide du jeu pour les joueurs
        print("")
        print("Pour faire une action, c'est-à-dire faire une offre ou alors accepter une offre, envoyez un SIGUSR1 sur ton terminal")
        print("Pour annoncer que toutes vos cartes sont identiques, et donc que vous avez gagné, envoyez un SIGUSR2")
        print("")

        for i in range(nbJoueurs):  
            echange[i]=0
            offre[i]=0

        partie = Process(target = game, args = (nbJoueurs,echange,offre))  #on crée la partie
        partie.start()


        while endOfGame == False :  #permet de prendre les inputs et d'envoyer leurs résulatats au handler/player
            mess= askQueue.get()  #on regarde quel input il faut réaliser selon le message reçu dans la queue
            if mess == 1:  
                qui = int(input("Qui fait l'action? : "))
                askQueue.put(qui)
                quoi = input(" Quel type d'action voulez vous faire (o pour faire une offre, a pour accepter) : ")
                askQueue.put(quoi)
            if mess == 2:
                combien = int(input(" Combien de carte voulez vous offrir? : "))
                askQueue.put(combien)
            if mess == 3:
                num_offre = int(input("De quel joueur voulez vous accepter l'offre? : "))
                askQueue.put(num_offre)
            if mess == 4:
                stri = "Quel est la position de la carte que vous voulez envoyer ? : "
                posCarte = int(input(stri))
                askQueue.put(posCarte)
            if mess == 5:
                gagnant = int(input("Qui a sonné la cloche ? "))
                askQueue.put(gagnant)
        partie.join()
        partie.close()
        print("La partie s'arrete")
        jouer = int(input("Voulez-vous rejouer ? Entrer 0 pour oui ou 1 pour non"))
        print(jouer)

