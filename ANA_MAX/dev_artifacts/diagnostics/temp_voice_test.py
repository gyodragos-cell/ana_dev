from tools.edge_tts_voice import EdgeTTSVoice

voice = EdgeTTSVoice()
voice.execute('speak', text='Voice engine is active. I will read all messages aloud.', **{'async': False})
