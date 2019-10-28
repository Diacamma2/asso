Reçus fiscaux
=============

Pour les associations agréées à délivrer des reçus fiscaux, *Diacamma* vous permet de les générer.

Configuration
-------------

Afin de réaliser au mieux ces reçus fiscaux, voilà quelque configuration à vérifier:

**Indiquer le codes comptables soumis à reçu**
Menu *Administration > Configuration générale*, onglet *Adhérents*, champ "code comptable des reçus fiscaux"
Séléctionnez ici les codes de produit correspondant à un revenu soumis à une déduction fiscale.
Après rafraîchissement de l'application, un nouveau menu *Comptabilité > Reçus fiscaux* apparaît.

**Ajouter une image de signature.**
Une fois ajouté dans le gestionnaire de documentation, référencez la comme tel depuis le menu *Administration > Configuration générale*, onglet *Gestion documentaire*, champ "image de cachet ou de signature".
Cette image sera ajouter dans le document PDF du reçu dans la zone "signature" du modèle d'impression par défaut.
 
**Préciser la justification du reçu fiscal.**
L'association doit indiquer sur les reçu à quel titre elle peut les émettre.
En général, elle précise la date de parution au JO de sa situation d'utilité publique.
Rajouter donc cette mention depuis le menu *Général > Nos coordonnées* en éditant la fiche et l'ajoutant sur le terme "N° SIRET/SIREN"
Ce champ est ajouté par défaut en pied de page sur le reçu.

**Ajouter le logo de votre structure.**
Afin d'éviter d'avoir un logo par défaut dans vos reçus fiscaux en PDF, modifiez le logo de votre association.
Depuis le menu *Général > Nos coordonnées*, éditez la fiche et associez lui une image.


Génération
----------

Depuis le menu *Comptabilité > Reçus fiscaux*, on peux visualiser les reçus fiscaux déjà réalisés et filtrés par année civile.

	.. image:: taxreceipts.png

L'ensemble des reçus est généré manuellement, par année civil, via un bouton *Contrôle* (en bas à droite):

 - L'outil recherche toutes les lignes d'écritures validées avec les codes (précisés en configuration) non déjà associé à un reçu fiscal.
C'est son montant qui sera reporté sur le reçu.
L'outil regarde alors le tiers associés (unique).
*Celui-ci doit être lettré garantissant qu'il est bien soldé.*

 - L'outil recherche donc tout les écritures associées à son lettrage.
Toutes ses écritures doivent être également validées.

 - Et de là, l'outil extrait l'ensemble des règlements.
C'est ces règlements, et en particulier le dernier, qui font foi pour le reçu fiscal.
C'est donc sur l'année de ce dernier règlement que sera constitué le reçu fiscal.
Si le règlement est réalisé sur un autre exercice, c'est l'année de règlement qui fera foi comme date du reçu fiscal.

 - Attribution d'un numéro unique par année civil de ce nouveau reçu fiscal.

 - Possibilité de gérer des reçus fiscaux pour "abandon de frais": à la place d'une écriture de règlement, c'est une écriture de charge qui est lettré avec l'écriture d'origine défiscalisable.

Une fois généré, chaque reçu pourra être imprimé en PDF ainsi qu'envoyer par courriel (comme les factures).

**Attention:** la génération de reçus fiscaux est définitive. Comme ils correspondent à la réalité d'une comptabilité validée, il n'est pas possible de les corriger ou de les annuler.

**Note:** Une version PDF des reçus est automatiquement sauvegardée dans le gestionnaire de document dans un répertoire ayant pour nom l'année civile. Si ce répertoire n'existe pas, il est créé.

