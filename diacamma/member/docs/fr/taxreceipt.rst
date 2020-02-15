Reçus fiscaux
=============

Si votre association est d'intérêt général, elle peut délivrer des reçus fiscaux à ses donateurs et à ses membres. Vous pouvez utiliser *Diacamma* pour cela.

Configuration
-------------

**Indiquer les codes comptables des produits pouvant donner droit à une déduction fiscale**

     Menu *Administration/Configuration générale* - onglet "Adhérents"

Mettez à jour le champ "code comptable des reçus fiscaux" avec les comptes de produits concernés.
Après rafraîchissement de l'application, le menu *Comptabilité/Reçus fiscaux* est maintenant disponible.


**Ajouter une image de signature**

     Menu *Bureautique/Gestion de fichiers et de documents/Documents*

Ajoutez dans le *Gestionnaire de documents* le fichier image devant être utilisé comme cachet ou signature de votre association.

     Menu *Administration/Configuration générale* - onglet "Gestion documentaire"

Dans un second temps, mettez à jour le champ "image de cachet ou de signature".
Cette image, intégrée dans le modèle d'impression par défaut, sera insérée automatiquement dans le reçu au format PDF, zone "signature".
 

**Préciser la justification du reçu fiscal**

L'association doit indiquer sur les reçus à quel titre elle les émet ce reçu.
En général, elle précise la date de parution au Journal Officiel de sa situation d'utilité publique.


     Menu *Général/Nos coordonnées*

Éditez la fiche de votre association et renseignez le champ "N° SIRET/SIREN". Ce champ est ajouté par défaut en pied de page du reçu.


**Ajouter le logo de votre structure**

Afin d'éviter d'avoir le logo par défaut dans vos reçus, enregistrez sous *Diacamma* le logo de votre association.

     Menu *Général/Nos coordonnées*

Éditez la fiche de votre association et associez-lui une image.


Génération des reçus
--------------------
     
     Menu *Comptabilité/Reçus fiscaux*
     
Visualisez les reçus fiscaux déjà produits et filtrez-les sur l'année civile.
L'ouverture du droit à déduction fiscale nait du règlement du produit ouvrant droit à déduction. C'est pour cela que le reçu fiscal est établi sur l'année du règlement. En cas de règlement fractionné, c'est le dernier versement qui fait naître le droit à déduction.

	.. image:: taxreceipts.png

Les reçus fiscaux de l'année sélectionnée peuvent être générés, via le bouton "Contrôle" (situé en bas à droite) :

 * L'outil extrait tous les mouvements satisfaisant aux conditions suivantes :
 
    * les codes comptables doivent correspondre à des produits ouvrant droit à déduction fiscale (Menu */Configuration générale*)
    * les écritures associées doivent avoir été validées
    * les créances liées aux mouvements doivent être lettrées afin d'attester qu'elles sont bien réglées
    * le règlement doit avoir eu lieu sur l'année spécifiée
    * les mouvements ne doivent pas être déjà associés à des reçus fiscaux

Les mouvements satisfaisant à ces cinq conditions sont reportés dans le reçu de chaque tiers concerné.

 * Attribution d'un numéro unique (spécifique à l'année civile) à tout reçu fiscal
 * Possibilité de gérer des reçus fiscaux pour "abandon de frais"
 	Ces dons peuvent prendre plusieurs formes (argent, abandon de revenus ou de produits, renonciation expresse à des frais engagés dans le cadre d’une activité bénévole respectant certaines conditions)

Une fois généré, chaque reçu pourra être imprimé en PDF et pourra être envoyé par courriel (tout comme les factures).

**Attention :** la génération de reçus fiscaux est définitive. Comme ils correspondent à la réalité d'une comptabilité validée, il n'est pas possible de les corriger ou de les annuler.

**Note:** Une version PDF des reçus est automatiquement sauvegardée dans le *Gestionnaire de documents*, dans un répertoire ayant pour nom l'année civile. Si ce répertoire n'existe pas, il est créé.
