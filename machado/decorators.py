# Copyright 2018 by Embrapa.  All rights reserved.
#
# This code is part of the machado distribution and governed by its
# license. Please see the LICENSE.txt and README.md files that should
# have been included as part of this package for licensing information.

"""Decorators."""
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value
from django.db.models.functions import Concat


def get_feature_display(self):
    """Get the display feature prop."""
    try:
        return self.Featureprop_feature_Feature.get(
            type__name='display',
            type__cv__name='feature_property').value
    except ObjectDoesNotExist:
        return None


def get_feature_description(self):
    """Get the description feature prop."""
    try:
        return self.Featureprop_feature_Feature.get(
            type__name='description',
            type__cv__name='feature_property').value
    except ObjectDoesNotExist:
        return None


def get_feature_note(self):
    """Get the note feature prop."""
    try:
        return self.Featureprop_feature_Feature.get(
            type__name='note',
            type__cv__name='feature_property').value
    except ObjectDoesNotExist:
        return None


def get_feature_orthologs_groups(self):
    """Get the orthologous group id."""
    result = list()
    feature_relationships = self.FeatureRelationship_subject_Feature.filter(
        type__name='in orthology relationship with',
        type__cv__name='relationship').distinct("value")
    for feature_relationship in feature_relationships:
        result.append(feature_relationship.value)
    return result


def machadoFeatureMethods():
    """Add methods to machado.models.Feature."""
    def wrapper(cls):
        setattr(cls, 'get_display', get_feature_display)
        setattr(cls, 'get_description', get_feature_description)
        setattr(cls, 'get_note', get_feature_note)
        setattr(cls, 'get_orthologs_groups', get_feature_orthologs_groups)
        return cls
    return wrapper


def get_pub_authors(self):
    """Get a publication string."""
    return ', '.join(self.Pubauthor_pub_Pub.order_by(
        'rank').annotate(author=Concat(
            'surname', Value(' '), 'givennames')).values_list(
                'author', flat=True))


def get_pub_doi(self):
    """Get a publication DOI."""
    return self.PubDbxref_pub_Pub.filter(
        dbxref__db__name='DOI').first().dbxref.accession


def machadoPubMethods():
    """Add methods to machado.models.Pub."""
    def wrapper(cls):
        setattr(cls, 'get_authors', get_pub_authors)
        setattr(cls, 'get_doi', get_pub_doi)
        return cls
    return wrapper
