from sentence_transformers import SentenceTransformer, util
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize
from faster_whisper import WhisperModel
import json
from flask import Flask, request, jsonify
from typing import List

class SentenceTransformersSimilarity():
    def __init__(self, similarity_threshold, model='intfloat/e5-large'):
        self.model = SentenceTransformer(model)
        self.similarity_threshold = similarity_threshold


    def similarities(self, sentences: List[str]):
        # Encode all sentences
        embeddings = self.model.encode(sentences)

        # Calculate cosine similarities for neighboring sentences
        similarities = []
        for i in range(1, len(embeddings)):
            sim = util.pytorch_cos_sim(embeddings[i-1], embeddings[i]).item()
            similarities.append(sim)

        return similarities

class SimilarSentenceSplitter():

    def __init__(self, similarity_model):
        self.model = similarity_model

    def split(self, text: str, group_max_sentences=5) -> List[str]:
        '''
            group_max_sentences: The maximum number of sentences in a group.
        '''
        sentences = text

        if len(sentences) == 0:
            return []

        similarities = self.model.similarities(sentences)
        # The first sentence is always in the first group.
        groups = [[sentences[0]]]
        # Using the group min/max sentences contraints,
        # group together the rest of the sentences.
        for i in range(1, len(sentences)):
            if len(groups[-1]) >= group_max_sentences:
                groups.append([sentences[i]])
            elif similarities[i-1] >= self.model.similarity_threshold:
                groups[-1].append(sentences[i])
            else:
                groups.append([sentences[i]])

        return groups
    
class AudioRecognition():
  def __init__(self, whisper_size = 'Systran/faster-whisper-large-v3', similarity_model = 'intfloat/multilingual-e5-large', similarity_threshold=0.84):
    self.whisper_model = WhisperModel(whisper_size, device="cuda")
    self.sentence_transformer = SentenceTransformersSimilarity(similarity_threshold, similarity_model)
    self.spliter = SimilarSentenceSplitter(self.sentence_transformer)

  def speech_recognition(self, url):
      segments, info = self.whisper_model.transcribe(url, beam_size=5)
      transcription = []
      seg = []
      for segment in segments:
        text = segment.text
        start = segment.start
        end = segment.end
        transcription.append(text[1:])
        seg.append([end, text[1:]])
      return info[0], transcription, seg
  def audio_recognition(self, url):
      '''
      Возвращает картеж из распознанного языка и массива,
       в котором похожие по теме предложения обьеденены.
      '''
      lang, text, seg = self.speech_recognition(url)
      chunked_text = self.spliter.split(text)
      end_time = []
      for i in chunked_text:
        chunk = "".join(j for j in i)
        end_time.append(0)
        for s in seg:
          if s[1] in chunk and s[0]>end_time[-1]:
            end_time[-1] = s[0]
        if end_time[-1]==0:
          for s in seg:
            if s[0]>end_time[-2]:
              end_time[-1]=s[0]
              break
      result = []
      for i in range(len(chunked_text)):
        result.append({'interval':i, 'text':chunked_text[i], 'end_interval':end_time[i]})
      return lang, result
