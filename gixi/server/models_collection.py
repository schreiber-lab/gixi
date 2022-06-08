from torchvision.ops import box_iou

from .model import (
    TwoStageDetector,
    VCompressResNet,
    BackboneWithFPN,
    RoiAlign,
    ChooseOneMap,
    Matcher,
)

from gixi.server.app_config import AppConfig


def get_basic_model_1(config: AppConfig):
    device = config.device
    model_name = config.model_config.name

    backbone = BackboneWithFPN(
        VCompressResNet(
            channels=(64, 128, 256, 256),
            include_features_list=[2, 3, 4],
        ),
        backbone_channels=[128, 256, 256],
        out_channels=64,
    )

    roi_align = RoiAlign(
        height=16, width=16,
        choose_map=ChooseOneMap(0, 3),
        feature_map_sizes=backbone.feature_map_sizes(),
    )

    model = TwoStageDetector(
        backbone,
        height_weight_per_feature=(
            ((50, 10), (100, 10)),
            ((200, 10), (300, 10)),
            ((400, 10), (500, 10)),
        ),
        representation_size=32,
        rpn_matcher=Matcher(0.34, 0.15, True),
        roi_matcher=Matcher(0.3, 0.01, False),
        rpn_reg_weight=10,
        box_weight=10,
        rpn_box_similarity=box_iou,
        roi_align=roi_align,
        nms_thresh=config.postprocessing_config.nms_level,
        score_thresh=config.postprocessing_config.score_level,
    ).to(device).eval()

    model.load_model(model_name, device=device)
    return model
