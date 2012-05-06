import os
import re
import sys
import optparse

import envoy
import requests

LANGUAGE_CODES = ['sk', 'uk', 'us', 'au']

DICTIONARY_BASE_URL = 'http://www.seslisozluk.net'
DICTIONARY_SEARCH_URL = '?'.join([DICTIONARY_BASE_URL, 'ssQBy=0&word=%s'])
AUDIO_LINK_PATTERN = re.compile("listen_word\('(%s)','([^']+)'" % '|'.join(LANGUAGE_CODES))

AUDIO_CACHE_DIR = '/tmp'


def say(text, options):
    repeat = options.repeat
    language = options.language
    audio_file = os.path.join(
        AUDIO_CACHE_DIR, 
        '{text}_{language}.mp3'.format(
            text='_'.join(text.split()),
            language=language
        )
    )
    
    def play():
        for i in xrange(repeat):
            played = envoy.run('play %s' % audio_file)
        
            if not played.status_code == 0:
                print 'Ops! Something goes wrong!'
                sys.exit()
    
    # play from cache if exists
    if os.path.exists(audio_file):
        play()
        sys.exit()
    
    # fetch the page
    response = requests.get(DICTIONARY_SEARCH_URL % text)
    
    status_code = response.status_code
    
    if status_code != 200:
        print 'HTTP error: %s' % status_code
    
    # find audio links
    audio_links = dict(AUDIO_LINK_PATTERN.findall(response.content))
    
    # check if selected language exists
    if language not in audio_links:
        print 'Audio file for "%s" language does not exists' % language
        sys.exit()
    
    audio_link = audio_links[language]
    
    # fetch audio file
    response = requests.get('/'.join([DICTIONARY_BASE_URL, audio_link]))
    
    if response.status_code != 200:
        print 'Audio file %s could not be downloaded' % audio_link
        sys.exit()
    
    # cache audio file
    with open(audio_file, 'w') as f:
        f.write(response.content)
    
    play()

def main():
    optparser = optparse.OptionParser()
    optparser.add_option('-l', '--language', dest='language', default='en')
    optparser.add_option('-r', '--repeat', dest='repeat', default=1, type='int')
    
    (options, args) = optparser.parse_args()
    
    if not args:
        print 'Missing text'
        sys.exit()
    
    if len(args) > 1:
        print 'Unknown arguments: ' % ', '.join(args[1:])
        sys.exit()
    
    if options.language == 'en':
        options.language = 'sk'
    
    if options.language not in LANGUAGE_CODES:
        print 'Unknown language: %s' % options.language
        sys.exit()
    
    say(args.pop(), options)

if __name__ == '__main__':
    main()
