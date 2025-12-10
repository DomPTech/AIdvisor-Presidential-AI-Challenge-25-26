import torch
import torch.nn as nn

class DisasterPredictionModel(nn.Module):
    def __init__(self):
        super(DisasterPredictionModel, self).__init__()
        self.fc = nn.Linear(10, 1) # Placeholder layers

    def forward(self, x):
        return self.fc(x)

def predict(data):
    """
    Placeholder prediction function.
    """
    return 0.5
