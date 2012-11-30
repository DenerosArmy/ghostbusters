//
//  GHViewController.h
//  PanicAR-Demo
//
//  Created by Sumukh Sridhara on 11/29/12.
//  Copyright (c) 2012 doPanic. All rights reserved.
//

#import <UIKit/UIKit.h>

@interface GHViewController : UIViewController {
    
    AVCaptureSession *cameraCaptureSession;
    AVCaptureVideoPreviewLayer *cameraPreviewLayer;
    IBOutlet UIButton *snap;
    NSMutableArray *valuescomp;
    
    
}
@property (nonatomic,strong) IBOutlet UIButton *snap;
@property (nonatomic, strong) NSString *store;
@property (nonatomic, strong) NSMutableArray *valuescomp;


- (void) initializeCaptureSession;
- (IBAction)snap:(id)sender;


@end
