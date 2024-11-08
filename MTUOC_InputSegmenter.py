#    MTUOC-SRXSegmenter
#    Copyright (C) 2024  Antoni Oliver
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


import argparse
import sys
import codecs

#SRX_SEGMENTER
import lxml.etree
import regex
from typing import (
    List,
    Set,
    Tuple,
    Dict,
    Optional
)

class SrxSegmenter:
    """Handle segmentation with SRX regex format.
    """
    def __init__(self):
        self.srx_file=None
        self.source_text = ""
        self.rules={}
        self.non_breaks=None
        self.breaks=None
        self.srxlang="Catalan"
        #self.non_breaks = rule.get('non_breaks', [])
        #self.breaks = rule.get('breaks', [])
        
    def set_srx_file(self, srxfile):
        self.srx_file=srxfile
        
    def parse(self) -> Dict[str, Dict[str, List[Tuple[str, Optional[str]]]]]:
        """Parse SRX file and return it.
        :param srx_filepath: is soruce SRX file.
        :return: dict
        """
        tree = lxml.etree.parse(self.srx_file)
        namespaces = {
            'ns': 'http://www.lisa.org/srx20'
        }

        rules = {}

        for languagerule in tree.xpath('//ns:languagerule', namespaces=namespaces):
            rule_name = languagerule.attrib.get('languagerulename')
            if rule_name is None:
                continue

            current_rule = {
                'breaks': [],
                'non_breaks': [],
            }
            for rule in languagerule.xpath('ns:rule', namespaces=namespaces):
                is_break = rule.attrib.get('break', 'yes') == 'yes'
                rule_holder = current_rule['breaks'] if is_break else current_rule['non_breaks']

                beforebreak = rule.find('ns:beforebreak', namespaces=namespaces)
                beforebreak_text = '' if beforebreak.text is None else beforebreak.text

                afterbreak = rule.find('ns:afterbreak', namespaces=namespaces)
                afterbreak_text = '' if afterbreak.text is None else afterbreak.text

                rule_holder.append((beforebreak_text, afterbreak_text))

            self.rules[rule_name] = current_rule
        
        

    def _get_break_points(self, regexes: List[Tuple[str, str]]) -> Set[int]:
        return set([
            match.span(1)[1]
            for before, after in regexes
            for match in regex.finditer('({})({})'.format(before, after), self.source_text)
        ])

    def get_non_break_points(self) -> Set[int]:
        """Return segment non break points
        """
        return self._get_break_points(self.non_breaks)

    def get_break_points(self) -> Set[int]:
        """Return segment break points
        """

    def extract(self,source_text) -> Tuple[List[str], List[str]]:
        """Return segments and whitespaces.
        """
        non_break_points = self.get_non_break_points()
        candidate_break_points = self.get_break_points()

        break_point = sorted(candidate_break_points - non_break_points)
        source_text = self.source_text

        segments = []  # type: List[str]
        whitespaces = []  # type: List[str]
        previous_foot = ""
        for start, end in zip([0] + break_point, break_point + [len(source_text)]):
            segment_with_space = source_text[start:end]
            candidate_segment = segment_with_space.strip()
            if not candidate_segment:
                previous_foot += segment_with_space
                continue

            head, segment, foot = segment_with_space.partition(candidate_segment)

            segments.append(segment)
            whitespaces.append('{}{}'.format(previous_foot, head))
            previous_foot = foot
        whitespaces.append(previous_foot)

        return segments, whitespaces
        
    def segment(self,cadena):
        srxSegmenter=SrxSegmenter(self.rules[self.srxlang],cadena)
        segments=segmenter.segment()
        return(segments)


