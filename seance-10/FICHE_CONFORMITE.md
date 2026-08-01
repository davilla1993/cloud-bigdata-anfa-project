# Fiche de conformité — Application mobile passagers Anfa

> Gabarit fourni. Complétez chaque section **en 2-4 lignes**, en vous appuyant sur le CM.
> Il n'y a pas de "bonne réponse" unique sur certains points — l'important est le raisonnement.

## 1. Finalité du traitement
La position GPS sert uniquement à proposer le trajet le plus proche, l'historique de paiements mobile
money à gérer l'abonnement, et le numéro de téléphone à identifier le compte. Chaque donnée a un usage
précis et délimité : par exemple, réutiliser la position GPS pour du profilage commercial ou revendre
l'historique de paiements à un tiers constituerait un détournement de finalité interdit sans nouvelle
base légale (principe de finalité, RGPD/loi togolaise).

## 2. Données collectées et leur sensibilité
Les 3 données : position GPS, historique de paiements mobile money, numéro de téléphone. La **position
GPS** est la plus sensible : collectée en continu, elle permet de reconstituer les déplacements d'une
personne (domicile, lieu de travail, habitudes) bien au-delà du simple trajet ponctuel — c'est le
risque de géolocalisation identifiante évoqué en CM. L'historique de paiements est également sensible
(donnée financière), et le numéro de téléphone, bien que moins sensible isolément, est ce qui permet de
relier les deux autres à une personne physique précise.

## 3. Base légale applicable
La position GPS et le numéro de téléphone relèvent de la **Loi n°2019-014** (protection des données à
caractère personnel), car ce sont des données identifiant une personne physique. L'historique de
paiements mobile money relève **à la fois** de la Loi 2019-014 (il identifie une personne) **et** de la
Loi 2017-007 modifiée par la Loi 2023-012 (transactions électroniques), car ce sont aussi des paiements
électroniques — exactement le cas cité en CM : une même donnée peut relever de deux textes à la fois,
et une plateforme conforme doit satisfaire les deux.

## 4. Durée de conservation
Par principe de minimisation, chaque donnée n'est gardée que le temps nécessaire à sa finalité : la
position GPS ne devrait pas être conservée au-delà de la durée du trajet en cours (sauf agrégation
anonymisée pour des statistiques d'affluence, qui est un autre usage nécessitant sa propre base légale).
L'historique de paiements peut nécessiter une conservation plus longue pour des raisons comptables, mais
pas indéfiniment. Le numéro de téléphone est conservé tant que le compte reste actif, puis supprimé ou
anonymisé.

## 5. Hébergement et souveraineté
Pour rester conformes à la loi togolaise 2019-014 et pouvoir démontrer cette conformité auprès de
l'autorité nationale de contrôle, ces données doivent rester hébergées sous juridiction togolaise —
c'est exactement le raisonnement derrière le choix 100% local/open source (MinIO, Postgres) fait depuis
la séance 1. Héberger chez un cloud américain exposerait ces données au **Patriot Act** : les autorités
américaines pourraient légalement y accéder même si le datacenter physique est situé ailleurs, ce qui
crée un conflit de juridiction et complique la conformité avec la loi togolaise.

## 6. Droit des personnes concernées
Oui : la Loi 2019-014 (comme le RGPD dont elle s'inspire) prévoit un droit à l'oubli permettant à un
passager de demander la suppression de ses données. La plateforme Anfa telle que construite depuis la
séance 1 n'a pas été pensée avec ce droit en tête — il n'existe pas de mécanisme pour retrouver et
supprimer toutes les données d'un passager donné à travers MinIO, Postgres, etc. Cela illustre
précisément le principe de "privacy by design" vu en CM : cette capacité doit se penser dès la
conception du pipeline, pas s'ajouter après coup une fois la plateforme déjà construite.
