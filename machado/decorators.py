# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Decorators."""
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, F, Q
from django.db.models.functions import Concat


def get_feature_dbxrefs(self):
    """Get the feature dbxrefs."""
    result = list()
    for feature_dbxref in self.FeatureDbxref_feature_Feature.all():
        if feature_dbxref.dbxref.db.url:
            result.append(
                "<a href='{}://{}{}' target='_blank'>{}:{}</a>".format(
                    feature_dbxref.dbxref.db.urlprefix,
                    feature_dbxref.dbxref.db.url,
                    feature_dbxref.dbxref.accession,
                    feature_dbxref.dbxref.db.name,
                    feature_dbxref.dbxref.accession,
                )
            )
        else:
            result.append(
                "{}:{}".format(
                    feature_dbxref.dbxref.db.name, feature_dbxref.dbxref.accession
                )
            )
    return result


def get_feature_product(self):
    """Get the product feature prop."""
    try:
        return self.Featureprop_feature_Feature.get(
            type__name="product", type__cv__name="feature_property"
        ).value
    except ObjectDoesNotExist:
        return None


def get_feature_description(self):
    """Get the description feature prop."""
    try:
        return self.Featureprop_feature_Feature.get(
            type__name="description", type__cv__name="feature_property"
        ).value
    except ObjectDoesNotExist:
        return None


def get_feature_note(self):
    """Get the note feature prop."""
    try:
        return self.Featureprop_feature_Feature.get(
            type__name="note", type__cv__name="feature_property"
        ).value
    except ObjectDoesNotExist:
        return None


def get_feature_annotation(self):
    """Get the annotation feature prop."""
    try:
        fps = self.Featureprop_feature_Feature.filter(
            type__name="annotation", type__cv__name="feature_property"
        )
        annotations = list()
        for fp in fps:
            try:
                doi = fp.FeaturepropPub_featureprop_Featureprop.get().pub.get_doi()
                annotations.append("{} (DOI:{})".format(fp.value, doi))
            except ObjectDoesNotExist:
                annotations.append(fp.value)
        return annotations
    except ObjectDoesNotExist:
        return None


def get_feature_doi(self):
    """Get the DOI feature."""
    dois = set()
    pubs = self.FeaturePub_feature_Feature.filter()
    for featurepub in pubs:
        dois.add(featurepub.pub.get_doi())
    try:
        fps = self.Featureprop_feature_Feature.filter(
            type__name="annotation", type__cv__name="feature_property"
        )
        for fp in fps:
            try:
                doi = fp.FeaturepropPub_featureprop_Featureprop.get().pub.get_doi()
                dois.add(doi)
            except ObjectDoesNotExist:
                pass
        return dois
    except ObjectDoesNotExist:
        return None


def get_feature_display(self):
    """Get the display feature prop."""
    try:
        return self.Featureprop_feature_Feature.get(
            type__name="display", type__cv__name="feature_property"
        ).value
    except ObjectDoesNotExist:
        if self.get_product() is not None:
            return self.get_product()
        elif self.get_description() is not None:
            return self.get_description()
        elif self.get_note() is not None:
            return self.get_note()
        else:
            return None


def get_feature_properties(self):
    """Get all the feature properties."""
    attrs_bl = ["coexpression group", "coexpression group", "annotation"]
    try:
        return (
            self.Featureprop_feature_Feature.filter(type__cv__name="feature_property")
            .exclude(type__name__in=attrs_bl)
            .order_by("type__name")
            .values_list("type__name", "value")
        )
    except ObjectDoesNotExist:
        return list()


def get_feature_synonyms(self):
    """Get all the feature synonyms."""
    result = list()
    for feature_synonym in self.FeatureSynonym_feature_Feature.all():
        result.append("{}".format(feature_synonym.synonym.name))
    return result


def get_feature_orthologous_group(self):
    """Get the orthologous group id."""
    try:
        return self.Featureprop_feature_Feature.get(
            type__cv__name="feature_property", type__name="orthologous group"
        ).value
    except ObjectDoesNotExist:
        return None


def get_feature_coexpression_group(self):
    """Get the coexpression group id."""
    try:
        return self.Featureprop_feature_Feature.get(
            type__cv__name="feature_property", type__name="coexpression group"
        ).value
    except ObjectDoesNotExist:
        return None


def get_feature_expression_samples(self):
    """Get the expression samples and treatments."""
    try:
        return list(
            self.Analysisfeature_feature_Feature.annotate(
                assay_name=F(
                    "analysis__Quantification_analysis_Analysis__acquisition__assay__name"
                )
            )
            .annotate(
                assay_description=F(
                    "analysis__Quantification_analysis_Analysis__acquisition__assay__description"
                )
            )
            .annotate(
                biomaterial_name=F(
                    "analysis__Quantification_analysis_Analysis__acquisition__assay__AssayBiomaterial_assay_Assay__biomaterial__name"
                )
            )
            .annotate(
                biomaterial_description=F(
                    "analysis__Quantification_analysis_Analysis__acquisition__assay__AssayBiomaterial_assay_Assay__biomaterial__description"
                )
            )
            .annotate(
                treatment_name=F(
                    "analysis__Quantification_analysis_Analysis__acquisition__assay__AssayBiomaterial_assay_Assay__biomaterial__Treatment_biomaterial_Biomaterial__name"
                )
            )
            .filter(normscore__gt=0)
            .exclude(assay_name__isnull=True)
            .values(
                "analysis__sourcename",
                "normscore",
                "assay_name",
                "assay_description",
                "biomaterial_name",
                "biomaterial_description",
                "treatment_name",
            )
        )
    except ObjectDoesNotExist:
        return None


def get_feature_relationship(self):
    """Get the relationships."""
    if not hasattr(settings, "MACHADO_VALID_TYPES"):
        raise AttributeError("The setting of MACHADO_VALID_TYPES is required.")

    result = list()
    feature_relationships = self.FeatureRelationship_object_Feature.filter(
        Q(type__name="part_of") | Q(type__name="translation_of"),
        type__cv__name="sequence",
    )
    for feature_relationship in feature_relationships:
        if feature_relationship.subject.type.name in settings.MACHADO_VALID_TYPES:
            result.append(feature_relationship.subject)

    feature_relationships = self.FeatureRelationship_subject_Feature.filter(
        Q(type__name="part_of") | Q(type__name="translation_of"),
        type__cv__name="sequence",
    )
    for feature_relationship in feature_relationships:
        if feature_relationship.object.type.name in settings.MACHADO_VALID_TYPES:
            result.append(feature_relationship.object)

    return result


def get_feature_cvterm(self):
    """Get the cvterms."""
    return self.FeatureCvterm_feature_Feature.all().values(
        name=F("cvterm__name"),
        definition=F("cvterm__definition"),
        cv=F("cvterm__cv__name"),
        db=F("cvterm__dbxref__db__name"),
        dbxref=F("cvterm__dbxref__accession"),
    )


def get_feature_location(self):
    """Get the feature location."""
    result = list()
    for location in self.Featureloc_feature_Feature.all():
        jbrowse_url = None
        if hasattr(settings, "MACHADO_JBROWSE_URL"):
            if hasattr(settings, "MACHADO_JBROWSE_TRACKS"):
                tracks = settings.MACHADO_JBROWSE_TRACKS
            else:
                tracks = "ref_seq,gene,transcripts,CDS"
            if hasattr(settings, "MACHADO_JBROWSE_OFFSET"):
                offset = settings.MACHADO_JBROWSE_OFFSET
            else:
                offset = 1000
            if location.srcfeature is not None:
                loc = "{}:{}..{}".format(
                    location.srcfeature.uniquename,
                    location.fmin - offset,
                    location.fmax + offset,
                )
                organism = "{} {}".format(
                    location.srcfeature.organism.genus,
                    location.srcfeature.organism.species,
                )
                if location.srcfeature.organism.infraspecific_name is not None:
                    organism += " {}".format(
                        location.srcfeature.organism.infraspecific_name
                    )
                jbrowse_url = (
                    "{}/?data=data/{}&loc={}"
                    "&tracklist=0&nav=0&overview=0"
                    "&tracks={}".format(
                        settings.MACHADO_JBROWSE_URL, organism, loc, tracks
                    )
                )
                result.append(
                    {
                        "start": location.fmin,
                        "end": location.fmax,
                        "strand": location.strand,
                        "ref": location.srcfeature.uniquename,
                        "jbrowse_url": jbrowse_url,
                    }
                )
    return result


def machado_feature_methods():
    """Add methods to machado.models.Feature."""

    def wrapper(cls):
        setattr(cls, "get_dbxrefs", get_feature_dbxrefs)
        setattr(cls, "get_display", get_feature_display)
        setattr(cls, "get_product", get_feature_product)
        setattr(cls, "get_description", get_feature_description)
        setattr(cls, "get_note", get_feature_note)
        setattr(cls, "get_annotation", get_feature_annotation)
        setattr(cls, "get_doi", get_feature_doi)
        setattr(cls, "get_orthologous_group", get_feature_orthologous_group)
        setattr(cls, "get_coexpression_group", get_feature_coexpression_group)
        setattr(cls, "get_expression_samples", get_feature_expression_samples)
        setattr(cls, "get_relationship", get_feature_relationship)
        setattr(cls, "get_cvterm", get_feature_cvterm)
        setattr(cls, "get_location", get_feature_location)
        setattr(cls, "get_properties", get_feature_properties)
        setattr(cls, "get_synonyms", get_feature_synonyms)
        return cls

    return wrapper


def get_pub_authors(self):
    """Get a publication string."""
    return ", ".join(
        self.Pubauthor_pub_Pub.order_by("rank")
        .annotate(author=Concat("surname", Value(" "), "givennames"))
        .values_list("author", flat=True)
    )


def get_pub_doi(self):
    """Get a publication DOI."""
    return (
        self.PubDbxref_pub_Pub.filter(dbxref__db__name="DOI").first().dbxref.accession
    )


def machado_pub_methods():
    """Add methods to machado.models.Pub."""

    def wrapper(cls):
        setattr(cls, "get_authors", get_pub_authors)
        setattr(cls, "get_doi", get_pub_doi)
        return cls

    return wrapper
