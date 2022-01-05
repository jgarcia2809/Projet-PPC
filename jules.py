from multiprocessing import Process, Array
import time
from threading import Semaphore
import sysv_ipc


#Shared Memory 
joueur = []
# Offre et echange sont des Array du coup il est juste à declarer dans le main est accessible partout
MessQueue= sysv_ipc.MessageQueue(42)        #C'est par cette queue que vont se réaliser tout les échanges entre chaque joueur. Vu que les actions sont bloqué par le sempaohr du signal il ne peut pas y avoit plusieurs echange en meme temps donc pas besoin de plusieurs queue
semEchange = Semaphore(1)

def game(nbJoueur):
    decks = DistribCarte(nbJoueur)
    players = [ Process(target = player, args=(i,decks[i],)) for i in range(nbJoueur) ]

    


def player(id,deck):
    while 1==1:
        if echange[id]== 0:      #On est dans la parti d'échange
            found= False
            i=1
            while found == False :
                if i == id:
                    i=i+1
                if echange[i]== 0:
                    found = True
            if semEchange._value == 0 :             #Le sémaphore a été pris par l'autre joueur du coup ce joueur la se met en reception
                message, t = MessQueue.recieve()
                message = message.decode()
                cartes= message.split(";")




            
            



        fich= "joueur"+str(id)+".txt"
        with open(fich, "w") as fichier:
            fichier.write("Bonjour player "+str(id))
            fichier.write("\nVos cartes sont les suivantes : ")
            for i in range(len(deck)):
                fichier.write(deck[i]+" ")
            fichier.write("\nLes dernières annonces sont : ")
            for j in range(len(offre)):
                fichier.write("Joueur "+str(j)+" : "+str(offre[j])+" carte(s)")
                
        

def DistribCarte(nb):
    nb = nb

if __name__ == "__main__":
    nbJ= input("Combien de Joueur? :")
    offre = Array('i', range(nbJ), Lock= True)
    echange = Array('i', range(nbJ))
    game = Process(target = game, args=(nbJ,))
    game.start()
    game.join()
