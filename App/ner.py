from transformers import pipeline
import torch


class Ner_Extractor:
    """
    Labeling each token in sentence as named entity

    :param model_checkpoint: name or path to model
    :type model_checkpoint: string
    """

    def __init__(self, model_checkpoint: str):
        self.token_pred_pipeline = pipeline("token-classification",
                                            model=model_checkpoint,
                                            aggregation_strategy="average")


    @staticmethod
    def concat_entities(ner_result):
        """
        Concatenation entities from model output on grouped entities

        :param ner_result: output from model pipeline
        :type ner_result: list
        :return: list of grouped entities with start - end position in text
        :rtype: list
        """
        entities = []
        prev_entity = None
        prev_end = 0
        for i in range(len(ner_result)):

            if (ner_result[i]["entity_group"] == prev_entity) &\
               (ner_result[i]["start"] == prev_end):

                entities[i-1][2] = ner_result[i]["end"]
                prev_entity = ner_result[i]["entity_group"]
                prev_end = ner_result[i]["end"]
            else:
                entities.append([ner_result[i]["entity_group"],
                                 ner_result[i]["start"],
                                 ner_result[i]["end"]])
                prev_entity = ner_result[i]["entity_group"]
                prev_end = ner_result[i]["end"]

        return entities




    def get_entities(self, text: str):
        """
        Extracting entities from text with them position in text

        :param text: input sentence for preparing
        :type text: string
        :return: list with entities from text
        :rtype: list
        """
        assert len(text) > 0, text
        entities = self.token_pred_pipeline(text)
        concat_ent = self.concat_entities(entities)

        return concat_ent


    def show_ents_on_text(self, text: str):
        """
        Highlighting named entities in input text

        :param text: input sentence for preparing
        :type text: string
        :return: Highlighting text
        :rtype: string
        """
        assert len(text) > 0, text
        entities = self.get_entities(text)

        return self.colored_text(text, entities)

def unite_entities(extractor, text):
  entity_list = extractor.get_entities(text)

  output = []
  for i in range(len(entity_list)-1):
      if entity_list[i+1][1] - entity_list[i][2] == 1:
          output.append([entity_list[i][0], entity_list[i][1], entity_list[i+1][2]])
      else:
          output.append(entity_list[i])
  return output

extractor = Ner_Extractor(model_checkpoint = "surdan/LaBSE_ner_nerel")