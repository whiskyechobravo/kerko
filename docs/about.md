# About

Kerko was inspired by prior work accomplished by [Whisky Echo
Bravo][Whisky_Echo_Bravo] on two projects:

- [Bibliographie sur l’histoire de
  Montréal](https://bibliomontreal.uqam.ca/bibliographie/), developed in 2014 by
  David Lesieur and Patrick Fournier, of Whisky Echo Bravo, for the [Laboratoire
  d'histoire et de patrimoine de Montréal](https://lhpm.uqam.ca/) (Université du
  Québec à Montréal, Canada).
- [Bibliography on English-speaking Quebec](http://quescren.concordia.ca/),
  developed in 2017 by David Lesieur, for the [Quebec English-Speaking
  Communities Research Network
  (QUESCREN)](https://www.concordia.ca/artsci/scpa/quescren.html) (Concordia
  University, Canada).

In 2019, [Whisky Echo Bravo][Whisky_Echo_Bravo] was asked to work on another
similar project. That made it clear that a general solution would benefit many
organizations. However, software from the prior projects had to be rewritten in
order to be more adaptable to a variety of needs. That led to Kerko, whose
initial development was made possible through the following project:

- [Bibliographie francophone sur l'archivistique](https://bibliopiaf.ebsi.umontreal.ca/),
  funded by the
  [Association internationale des archives francophones (AIAF)](http://www.aiaf.org/)
  and hosted by the
  [École de bibliothéconomie et des sciences de l’information (EBSI)](https://ebsi.umontreal.ca/)
  (Université de Montréal, Canada).

Since then, Kerko has continued to evolve, thanks to work by [Whisky Echo
Bravo][Whisky_Echo_Bravo] and other contributors, often through funding provided
by organizations needing new features or customizations of Kerko.

## Design choices

Here are some of the design choices that have guided the development of Kerko so
far:

- Do not build back-end software. Let Zotero manage the data.
- Allow Kerko to integrate into richer web applications.
- Only provide features that pertain to the exploration of a bibliography.
  Other features, even when they are common to many web sites, do not belong to
  Kerko and should be left to the applications to implement.
- Use a lightweight framework to avoid carrying many features that are not
  needed by Kerko (Flask was selected for this reason).
- Use pure Python dependencies to keep installation and deployment simple (Hence
  the use of Whoosh for search, for example, instead of Elasticsearch or Solr).
- Use a classic server-side rendering architecture. Keep it simple and avoid
  asset management when possible.

## Etymology

The name _Zotero_ reportedly derives from the Albanian word _zotëroj_, which
means "to learn something extremely well, that is to master or acquire a skill
in learning" (Source: Mark Dingemanse, 2008, [Etymology of
Zotero](http://ideophone.org/zotero-etymology/)).

The name _Kerko_ is a nod to Zotero as it takes a similar etymological route: it
derives from the Albanian word _kërkoj_, which means "to ask, to request, to
seek, to look for, to demand, to search" and seems fit to describe a search
tool.


[Whisky_Echo_Bravo]: https://whiskyechobravo.com/
