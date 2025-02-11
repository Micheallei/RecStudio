from recstudio.data.dataset import MFDataset

from ..basemodel import BaseRanker
from ..loss_func import BCEWithLogitLoss
from ..module import ctr, MLPModule


class DeepFM(BaseRanker):

    def _get_dataset_class():
        return MFDataset

    def _init_model(self, train_data, drop_unused_field=True):
        super()._init_model(train_data, drop_unused_field)
        self.linear = ctr.LinearLayer(self.fields, train_data)
        self.fm = ctr.FMLayer(reduction='sum')
        self.embedding = ctr.Embeddings(self.fields, self.embed_dim, train_data)
        self.mlp = MLPModule([self.embedding.num_features*self.embed_dim]+self.config['mlp_layer']+[1],
                             self.config['activation'], self.config['dropout'],
                             last_activation=False, last_bn=False)

    def score(self, batch):
        lr_score = self.linear(batch)
        emb = self.embedding(batch)
        fm_score = self.fm(emb)
        mlp_score = self.mlp(emb.view(emb.size(0), -1)).squeeze(-1)
        return lr_score + fm_score + mlp_score

    def _get_loss_func(self):
        return BCEWithLogitLoss(self.rating_threshold)
