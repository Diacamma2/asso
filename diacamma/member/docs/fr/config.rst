Configuration
=============

Pour vous permettre d'exploiter au mieux le logiciel, certains paramétrages sont nécessaires.

Générale
--------

     Menu *Administration/Configuration générale*, onglet *Adhérents*
     
Vous pouvez modifier les paramètrages généraux relatifs à la gestion des adhésions.

	.. image:: conf_general.png


Saisons et cotisations
----------------------

     Menu *Administration/Modules (conf.)/Les saisons et les cotisations*
     
Vous pouvez modifier les paramètres de la gestion des licences sportives, en l'occurrence, les saisons sportives et les types de cotisations.

**Les Saisons**

	.. image:: season_list.png

Ici, vous pourrez ajouter de nouvelles saisons au fur et à mesure de l'utilisation du logiciel. Vous pourrez également déterminer la saison courante (dite active).
De plus, chaque saison est découpée en quatre périodes et en douze mois.

C'est la plus petite date de début et la plus grande de fin qui définissent la plage de votre saison. Vos saisons peuvent être d'une durée supérieure à un an et peuvent se chevaucher.
Vous pouvez modifier les dates de début et de fin de chaque période. Vous pouvez aussi ajouter ou supprimer une période, mais vous devez toujours en avoir au moins deux.
Deux périodes peuvent se chevaucher ou être disjointes (dans ce cas, un message d'avertissement vous prévient).
Le premier des douze mois commence le mois de la plus petite date de début de période. Même si votre saison couvre plus d'une année calendaire, il n'y aura pas de treizième mois dans votre saison.

Vous pouvez associer à chaque saison une liste de documents que chaque adhérent devra vous fournir pour finaliser son inscription.

	.. image:: documents.png

**Les types de cotisation**

	.. image:: cotisations.png

Ici vous pourrez saisir les différents types de cotisation proposés par votre association. Par exemple, pour une association pratiquant plusieurs activités sportives distinctes, vous pouvez avoir un type de cotisation pour chaque activité, un autre pour plusieurs de ces activités, et encore des types différents selon une pratique en compétition ou hors compétition des activités.

Quatre modes de durées différentes peuvent être affectées à un type de cotisation :

 - Annuelle : cotisation couvrant l'ensemble de la saison.
 - Périodique : cotisation couvrant une période (4 par défaut) de la saison.
 - Mensuelle : cotisation couvrant un des douze mois de la saison.
 - Calendaire : cotisation couvrant une année calendaire. Cette cotisation peut donc être à cheval sur deux saisons.

Pour le lien avec le module *Facturier* vous devez définir un prix de vente de votre cotisation en créant et en associant des articles.
Vous pouvez rattacher plusieurs articles à  une cotisation. Cela vous permet de distinguer, par exemple, la part de cotisation relative à votre club, de la licence de votre fédération.
Avec ces liens entre les cotisations et les articles,vous pourrez générer automatiquement des factures lors de vos procédures d'adhésion. Si une cotisation n'est liée au aucun article, aucune facture ne sera émise.

De même, vous pouvez aussi personnaliser le code comptable du tiers associé à vos adhérants dans le cas d'un création automatique.

**Les prestations**

Cette option est activable si vous utilisez les catégories d'équipes/cours.

Cela permet d'associer une équipe/cours à un article facturable afin de proposer un choix de prestations supplémentaires au moment de la saisie de la cotisation.

Vous choisissez vos prestations au moment de votre prise de cotisation. 
Automatiquement, votre adhérent est alors associé à la bonne catégorie d'équipes/cours définie par la prestation.
De plus, dans la facture d'adhésion est ajouté alors l'article relatif à cette prestation.  


Catégories
----------

Le menu *Administration/Modules (conf.)/Catégories* vous permet de modifier ce qui peut catégoriser un adhérent : les catégories d'âge, les équipes ou cours et les activités ainsi que la possibilité d'activer ou non ces différentes classifications.

Vous pouvez ne pas vouloir utiliser certaines catégories. Pour cela, désactivez-les depuis l'écran de paramétrage.
De la même façon, vous pouvez préciser si vous souhaitez pouvoir créer automatiquement une connexion par adhérent actif, afficher un numéro d'adhérent ou gérer des numéros de licence.
Vous pouvez également personnaliser la désignation 'équipe' et 'activité'.

	.. image:: categories.png

**Les âges**

Vous pourrez ici renseigner les catégories d'âges existantes dans votre association avec un nom de catégorie, une année (de naissance) de début et de fin de la catégorie.

Vous n'aurez pas besoin de changer les valeurs des années de naissance ultérieurement : le décalage est effectué automatiquement d'année en année.

	.. image:: age.png

**Les équipes/cours**

Vous gérez différentes équipes ou différents cours et vous souhaitez pouvoir gérer vos adhérents selon ce critère.
Renseignez-les ici, vous pourrez alors affecter des adhérents à ces équipes ou cours et ainsi les retrouver plus facilement.

	.. image:: team.png

**Les activités**

Vous gérez différentes activités (par exemple plusieurs arts martiaux) dans votre association ? Les renseigner ici vous permettra ensuite de classer vos adhérents en fonction de ces différentes activités, mais aussi de saisir pour eux plusieurs licences par an si nécessaire.

Exemple : une association regroupant judo et karaté, et donc affiliée à deux fédérations sportives différentes.
Vous pourriez alors saisir 2 licences par adhérent (sous réserve que vos adhérents pratiquent les deux sports et soient licenciés des deux fédérations).

	.. image:: activity.png
