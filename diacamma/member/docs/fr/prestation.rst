Prestations de cotisation
=========================

Cela permet d'associer une équipe/cours à un article facturable afin de proposer un choix de prestations supplémentaires au moment de la saisie de la cotisation.

Vous choisissez vos prestations au moment de votre prise de cotisation ou via un écran de gestion spécifique. 
Automatiquement, votre adhérent est alors associé à la bonne catégorie d'équipes/cours définie par la prestation.
De plus, dans la facture d'adhésion est ajouté alors l'article relatif à cette prestation.  

Pour activer ce mode, vous devez configurer dans le menu *Administration/Modules (conf.)/Catégories*, le paramètre *Activer les équipes* = "Avec prestation"
Une fois alors votre Diacamma rafraichi, un nouvelle écran *Association/Liste de prestations*

	.. image:: listprestation.png

Créer un prestation
-------------------

Depuis l'écran *Association/Liste de prestations*, il vous est possible de créer une nouvelle prestation.

Pour cela, cliquez sur le bouton "Créer".

	.. image:: newprestation.png
	
Vous pouvez alors créer une prestation soit en créant une équipe/cours, soit en l'associant à une existante.
Si vous gerez des activités, vous devez alors associer cette prestation à une activité existante.
De plus, vous devez également définir un article de facturation à cette prestation.

Vous pouvez bien entendu, ensuite modifier cette prestation: nom et description de son équipe/cours, son activité et son article.

Si vous le voulez alors, vous pouvez également lui associé d'autres articles afin que celle-ci comporte plusieurs tarif.
Cochez "Utiliser le multi-prix" pour que l'interface vous propose l'ajout, la modification ou la suppression d'un article de prix.

	.. image:: modifprestation.png

Si vous souhaitez supprimer une prestation, il vous sera demandé ce que vous souhaitez faire de l'équipe/cours associée: la désactiver, la supprimer ou la laisser.

Associer des pratiquants
------------------------

A chacune de ces prestations, vous pouvez bien sur ajouter des pratiquants.

	.. image:: showprestation.png
	
Via le bouton "Ajouter", rechercher une (ou plusieurs) fiche adhérent qui sera alors associé à cette prestation.
Vous pouvez de là également créer une nouvelle fiche.
Si cet adhérent n'est pas encore cotisant à votre structure, il vous sera demandé un type de cotisation. 
Si la cotisation a plusieurs prix possible, il vous sera demandé quelle tarification utiliser.

Dans le cas où un adhérent a sa cotisation "en création", les articles de la prestations choisis serons alors automatiquement ajouter au devis associé à cette cotisation.
Si sa cotisation est "validée", une facture est alors généré afin de prendre en compte cette nouvelle prestation.
Dans le cas où l'adhérent est retiré d'une prestation, un avoir équivalent est alors créé.  

Gérer des prestations
---------------------

Bien entendu, vos prestations ne sont pas figées.

Vous pouvez vouloir inverser des pratiquants, d'une prestation à une autre. 
Pour cela, cliquez sur "Permuter" après avoir sélectionné 2 prestations: un écran vous invitera à associer les bons pratiquants au bon groupe.

	.. image:: swapingprestation.png
	
Dans la même idée, le bouton "Dédoubler" vous permet de créer une nouvelle prestation d'après une ancienne et d'ensuite pouvoir permuter les pratiquants comme vous le souhaitez.

Le bouton "Fusion" permet, quand à lui, de fusionner en une seule prestation celles que vous aurez sélectionnées.
Les équipes/cours non conservées sont alors supprimées.

Avec cette gestion, la facturation s'en retrouvera alors automatiquement impacté avec la création de devis, facture ou avoir, suivant les modifications apportées.
