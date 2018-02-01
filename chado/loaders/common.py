"""cvterm library."""
from chado.loaders.exceptions import ImportingError
from chado.models import Cv, Cvterm, CvtermDbxref, Cvtermsynonym
from chado.models import Db, Dbxref
from django.core.exceptions import ObjectDoesNotExist
from django.db.utils import IntegrityError
import os
import re


class Validator(object):
    """Validate input file."""

    def validate(self, file_path):
        """Invoke all validations."""
        self._exists(file_path)
        self._is_file(file_path)
        self._is_readable(file_path)

    def _exists(self, file_path):
        """Check whether a file exists."""
        if not os.path.exists(file_path):
            raise ImportingError("{} does not exist".format(file_path))

    def _is_file(self, file_path):
        """Check whether file is actually a file type."""
        if not os.path.isfile(file_path):
            raise ImportingError("{} is not a file".format(file_path))

    def _is_readable(self, file_path):
        """Check file is readable."""
        try:
            f = open(file_path, 'r')
            f.close()
        except IOError:
            raise ImportingError("{} is not readable".format(file_path))


def process_cvterm_def(cvterm, definition):
    """Process defition to obtain cvterms."""
    text = ''

    '''
    Definition format:
    "text" [refdb:refcontent, refdb:refcontent]

    Definition format example:
    "A gene encoding an mRNA that has the stop codon redefined as
     pyrrolysine." [SO:xp]
    '''
    if definition:

        # Retrieve text and dbxrefs
        try:
            text, dbxrefs = definition.split('" [')
            text = re.sub(r'^"', '', text)
            dbxrefs = re.sub(r'\]$', '', dbxrefs)
        except ValueError:
            text = definition
            dbxrefs = ''

        if dbxrefs:

            dbxrefs = dbxrefs.split(', ')

            # Save all dbxrefs
            for dbxref in dbxrefs:
                ref_db, ref_content = dbxref.split(':', 1)

                if ref_db == 'http':
                    ref_db = 'URL'
                    ref_content = 'http:'+ref_content

                # Get/Set Dbxref instance: ref_db,ref_content
                db, created = Db.objects.get_or_create(name=ref_db)
                dbxref, created = Dbxref.objects.get_or_create(
                    db=db, accession=ref_content)

                # Estabilish the cvterm and the dbxref relationship
                CvtermDbxref.objects.get_or_create(cvterm=cvterm,
                                                   dbxref=dbxref,
                                                   is_for_definition=1)

    cvterm.definition = text
    cvterm.save()
    return


def process_cvterm_xref(cvterm, xref, is_for_definition=0):
    """Process cvterm_xref."""
    if xref:

        ref_db, ref_content = xref.split(':', 1)

        if ref_db == 'http':
            ref_db = 'URL'
            ref_content = 'http:'+ref_content

        # Get/Set Dbxref instance: ref_db,ref_content
        db, created = Db.objects.get_or_create(name=ref_db)
        dbxref, created = Dbxref.objects.get_or_create(
            db=db, accession=ref_content)

        # Estabilish the cvterm and the dbxref relationship
        CvtermDbxref.objects.get_or_create(cvterm=cvterm,
                                           dbxref=dbxref,
                                           is_for_definition=is_for_definition)
    return


def process_cvterm_go_synonym(cvterm, synonym, synonym_type):
    """Process cvterm_go_synonym.

    Definition format:
    "text" [refdb:refcontent, refdb:refcontent]

    Definition format example:
    "30S ribosomal subunit assembly" [GOC:mah]
    """
    # Retrieve text and dbxrefs
    text, dbxrefs = synonym.split('" [')
    synonym_text = re.sub(r'^"', '', text)
    synonym_type = re.sub(r'_synonym', '', synonym_type).lower()

    # Handling the synonym_type
    db_type, created = Db.objects.get_or_create(name='internal')
    dbxref_type, created = Dbxref.objects.get_or_create(
        db=db_type, accession=synonym_type)

    cv_synonym_type, created = Cv.objects.get_or_create(name='synonym_type')
    cvterm_type, created = Cvterm.objects.get_or_create(
        cv=cv_synonym_type,
        name=synonym_type,
        definition='',
        dbxref=dbxref_type,
        is_obsolete=0,
        is_relationshiptype=0)

    # Storing the synonym
    try:
        cvtermsynonym = Cvtermsynonym.objects.create(
            cvterm=cvterm,
            synonym=synonym_text,
            type_id=cvterm_type.cvterm_id)
        cvtermsynonym.save()
    # Ignore if already created
    except IntegrityError:
        pass

    return


def get_ontology_term(ontology, term):
    """Retrieve ontology term."""
    # Retrieve sequence ontology object
    try:
        cv = Cv.objects.get(name=ontology)
    except ObjectDoesNotExist:
        raise ObjectDoesNotExist(
            'Sequence Ontology not loaded ({}).'.format(ontology))

    # Retrieve sequence ontology term object
    try:
        cvterm = Cvterm.objects.get(cv=cv, name=term)
    except ObjectDoesNotExist:
        raise ObjectDoesNotExist(
            'Sequence Ontology term not found ({}).'.format(term))
    return cvterm