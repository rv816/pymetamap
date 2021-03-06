from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import zip
from builtins import str
from builtins import bytes
from builtins import *
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import subprocess
import tempfile
from .MetaMap import MetaMap
from .Concept import Corpus

class SubprocessBackend(MetaMap):
    def __init__(self, metamap_filename, version=None):
        """ Interface to MetaMap using subprocess. This creates a
            command line call to a specified metamap process.
        """
        MetaMap.__init__(self, metamap_filename, version)

    def extract_concepts(self, sentences=None, ids=None,
                         composite_phrase=4, filename=None, allow_concept_gaps=True,
                         file_format='sldi', allow_acronym_variants=False,
                         word_sense_disambiguation=True, allow_large_n=False,
                         no_derivational_variants=False,
                         derivational_variants=False, ignore_word_order=False,
                         unique_acronym_variants=False,
                         prefer_multiple_concepts=False,
                         ignore_stop_phrases=True,
                         restrict_to_vocabularies_list=['SNOMEDCT_US'],
                          compute_all_mappings=False, additional_options_list=[]):
        """ extract_concepts takes a list of sentences and ids(optional)
            then returns a list of Concept objects extracted via
            MetaMap.

            Supported Options:
                Composite Phrase -Q
                Word Sense Disambiguation -y
                allow large N -l
                No Derivational Variants -d
                Derivational Variants -D
                Ignore Word Order -i
                Allow Acronym Variants -a
                Unique Acronym Variants -u
                Prefer Multiple Concepts -Y
                Ignore Stop Phrases -K
                Compute All Mappings -b

            For information about the available options visit
            http://metamap.nlm.nih.gov/.

            Note: If an error is encountered the process will be closed
                  and whatever was processed, if anything, will be
                  returned along with the error found.
        """
        if allow_acronym_variants and unique_acronym_variants:
            raise ValueError("You can't use both allow_acronym_variants and "
                             "unique_acronym_variants.")
        if (sentences is not None and filename is not None) or \
                (sentences is None and filename is None):
            raise ValueError("You must either pass a list of sentences "
                             "OR a filename.")
        if file_format not in ['sldi','sldiID']:
            raise ValueError("file_format must be either sldi or sldiID")

        input_file = None
        if sentences is not None:
            input_file = tempfile.NamedTemporaryFile(delete=False)
        else:
            with open(filename, 'r') as f:
                input_file = f
        output_file = tempfile.NamedTemporaryFile(delete=False)
        error = None
        try:
            if sentences is not None:
                if ids is not None:
                    for identifier, sentence in zip(ids, sentences):
                        input_file.write(bytes('%r|%r\n' % (identifier, sentence), 'UTF-8'))
                else:
                    for sentence in sentences:
                        input_file.write(bytes('%r\n' % sentence, 'UTF-8'))
                input_file.flush()

            command = [self.metamap_filename, '-N']
            command.append('-Q')
            command.append(str(composite_phrase))
            if word_sense_disambiguation:
                command.append('-y')
            if allow_large_n:
                command.append('-l')
            if len(restrict_to_vocabularies_list)>0:
                command.append('-R {}'.format(str(','.join(restrict_to_vocabularies_list))))
            if no_derivational_variants:
                command.append('-d')
            if derivational_variants:
                command.append('-D')
            if allow_concept_gaps:
                command.append('-g')
            if ignore_word_order:
                command.append('-i')
            if allow_acronym_variants:
                command.append('-a')
            if unique_acronym_variants:
                command.append('-u')
            if prefer_multiple_concepts:
                command.append('-Y')
            if ignore_stop_phrases:
                command.append('-K')
            if compute_all_mappings:
                command.append('-b')
            if len(additional_options_list) > 0:
                for x in additional_options_list:
                    command.append(x)
            if ids is not None or (file_format == 'sldiID' and
                    sentences is None):
                command.append('--sldiID')
            else:
                command.append('--sldi')
            command.append(input_file.name)
            command.append(output_file.name)

            metamap_process = subprocess.Popen(command, stdout=subprocess.PIPE)
            while metamap_process.poll() is None:
                stdout = metamap_process.stdout.readline()
                if b'ERROR' in stdout:
                    metamap_process.terminate()
                    error = stdout.rstrip()

            output = output_file.read()
        finally:
            if sentences is not None:
                os.remove(input_file.name)
            else:
                input_file.close()
            os.remove(output_file.name)
            if not input_file.closed:
                input_file.close()
            if not output_file.closed:
                output_file.close()

        concepts = Corpus.load(output.splitlines())

        return (concepts, error)
