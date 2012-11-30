//
//  GHViewController.m
//  PanicAR-Demo
//
//  Created by Sumukh Sridhara on 11/29/12.
//  Copyright (c) 2012 doPanic. All rights reserved.
//

#import "GHViewController.h"
#import "SRWebSocket.h"
#import "SBJson.h"
@interface GHViewController () <SRWebSocketDelegate> {
    UIAccelerationValue gravX;
    UIAccelerationValue gravY;
    UIAccelerationValue gravZ;
    UIAccelerationValue prevVelocity;
    UIAccelerationValue prevAcce;
    
}
@property (strong) UIAccelerometer *sharedAcc;

@end

@implementation GHViewController
{
    SRWebSocket *_webSocket;
}
@synthesize sharedAcc = _sharedAcc;

@synthesize store;
@synthesize valuescomp;

#define kAccelerometerFrequency        50.0 //Hz
#define kFilteringFactor 0.1


- (id)initWithNibName:(NSString *)nibNameOrNil bundle:(NSBundle *)nibBundleOrNil
{
    self = [super initWithNibName:nibNameOrNil bundle:nibBundleOrNil];
    if (self) {
        // Custom initialization
    }
    return self;
}
- (UIAccelerationValue)tendToZero:(UIAccelerationValue)value {
    if (value < 0) {
        return ceil(value);
    } else {
        return floor(value);
    }
}

- (void)viewDidLoad
{
    [super viewDidLoad];
    NSLog(@"loaded");
    [self _reconnect];
    
    [self.navigationController setNavigationBarHidden:YES animated:YES];
    
    //[self hideTabBar:self.tabBarController];
    
    [self initializeCaptureSession];
    [self.view bringSubviewToFront:self.snap];
    NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
    
    
    // saving a Float
    [prefs setFloat:0.25 forKey:@"0"];
    [prefs setFloat:0.25 forKey:@"1"];
    [prefs setFloat:0.25 forKey:@"2"];
    [prefs setFloat:0.25 forKey:@"3"];
    [prefs synchronize];
    
    self.sharedAcc = [UIAccelerometer sharedAccelerometer];
    self.sharedAcc.delegate = self;
    self.sharedAcc.updateInterval = 1 / kAccelerometerFrequency;
    
    gravX = gravY = gravZ = prevVelocity = prevAcce = 0.f;
    
    
    
    
    // Do any additional setup after loading the view, typically from a nib.
    
    // Do any additional setup after loading the view from its nib.
    
    [NSTimer scheduledTimerWithTimeInterval:1    target:self    selector:@selector(didUpdateHeading)    userInfo:nil repeats:YES];
    [NSTimer scheduledTimerWithTimeInterval:1    target:self    selector:@selector(sender)    userInfo:nil repeats:YES];
    
    
    
    NSString *filePath = [[NSBundle mainBundle] pathForResource:@"fog" ofType:@"png"];
    UIImageView *img = [[UIImageView alloc] initWithImage:[UIImage imageWithContentsOfFile:filePath]];
    img.frame = CGRectMake(0, 0, [[UIScreen mainScreen] applicationFrame].size.width, [[UIScreen mainScreen] applicationFrame].size.height + 20);
    img.alpha = 1;
    img.tag = 12;
    [self.view addSubview:img];
    [self.view bringSubviewToFront:self.snap];
    
}

-(void)viewWillAppear:(BOOL)animated {
    
    [self _reconnect];
}


- (void)_reconnect {
    
    _webSocket.delegate = nil;
    [_webSocket close];
    
    _webSocket = [[SRWebSocket alloc] initWithURLRequest:[NSURLRequest requestWithURL:[NSURL URLWithString:@"ws://pyscript.denerosarmy.com:9000/data1"]]];
    _webSocket.delegate = self;
    
    [_webSocket open];
    
}

- (void)viewDidDisappear:(BOOL)animated
{
    [cameraCaptureSession stopRunning];
    cameraCaptureSession = nil;
    cameraPreviewLayer = nil;
    _webSocket.delegate = nil;
    [_webSocket close];
    _webSocket = nil;
    
}

- (void)viewDidUnload
{
    [super viewDidUnload];
    [cameraCaptureSession stopRunning];
    cameraCaptureSession = nil;
    cameraPreviewLayer = nil;
}
/*
 - (void)hideTabBar:(UITabBarController *) tabbarcontroller
 {
 [UIView beginAnimations:nil context:NULL];
 [UIView setAnimationDuration:0.5];
 
 for(UIView *view in tabbarcontroller.view.subviews)
 {
 if([view isKindOfClass:[UITabBar class]])
 {
 [view setFrame:CGRectMake(view.frame.origin.x, 584, view.frame.size.width, view.frame.size.height)];
 }
 else
 {
 [view setFrame:CGRectMake(view.frame.origin.x, view.frame.origin.y, view.frame.size.width, 584)];
 }
 }
 
 [UIView commitAnimations];
 }
 
 - (void)showTabBar:(UITabBarController *) tabbarcontroller
 {
 //should be off on the i5
 [UIView beginAnimations:nil context:NULL];
 [UIView setAnimationDuration:0.5];
 for(UIView *view in tabbarcontroller.view.subviews)
 {
 NSLog(@"%@", view);
 
 if([view isKindOfClass:[UITabBar class]])
 {
 [view setFrame:CGRectMake(view.frame.origin.x, 431, view.frame.size.width, view.frame.size.height)];
 
 }
 else
 {
 [view setFrame:CGRectMake(view.frame.origin.x, view.frame.origin.y, view.frame.size.width, 431)];
 }
 }
 
 [UIView commitAnimations];
 }
 */
-(void)sender {
    NSString *heading = [NSString stringWithFormat:@"%.2f", [[_sensorManager deviceAttitude] heading]];
    //convert object to data
    CLLocation* l = [[_sensorManager deviceAttitude] location];
    CLLocationCoordinate2D c = [l coordinate];
    NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
    float velocity = [prefs floatForKey:@"velocity"];
    
    
    NSString *args2 =  [NSString stringWithFormat: @"[%.4f,%.4f,%.2f,%i,%2f]", c.latitude,c.longitude,l.horizontalAccuracy,heading.intValue,velocity];
    
    NSDictionary *dic = [[NSDictionary alloc] initWithObjectsAndKeys:
                         @"compass", @"action", args2, @"args", nil]; //nil to signify end of objects and keys.
    
    [_webSocket send:[dic JSONRepresentation]];
    
    
}

- (void)accelerometer:(UIAccelerometer *)accelerometer didAccelerate:(UIAcceleration *)acceleration {
    gravX = (acceleration.x * kFilteringFactor) + (gravX * (1.0 - kFilteringFactor));
    gravY = (acceleration.y * kFilteringFactor) + (gravY * (1.0 - kFilteringFactor));
    gravZ = (acceleration.z * kFilteringFactor) + (gravZ * (1.0 - kFilteringFactor));
    
    UIAccelerationValue accelX = acceleration.x - ( (acceleration.x * kFilteringFactor) + (gravX * (1.0 - kFilteringFactor)) );
    
    UIAccelerationValue accelY = acceleration.y - ( (acceleration.y * kFilteringFactor) + (gravY * (1.0 - kFilteringFactor)) );
    UIAccelerationValue accelZ = acceleration.z - ( (acceleration.z * kFilteringFactor) + (gravZ * (1.0 - kFilteringFactor)) );
    accelX *= 9.81f;
    accelY *= 9.81f;
    accelZ *= 9.81f;
    accelX = [self tendToZero:accelX];
    accelY = [self tendToZero:accelY];
    accelZ = [self tendToZero:accelZ];
    
    UIAccelerationValue vector = sqrt(pow(accelX,2)+pow(accelY,2)+pow(accelZ, 2));
    UIAccelerationValue acce = vector - prevVelocity;
    UIAccelerationValue velocity = (((acce - prevAcce)/2) * (1/kAccelerometerFrequency)) + prevVelocity;
    
    //NSLog(@"X %g Y %g Z %g, Vector %g, Velocity %g",accelX,accelY,accelZ,vector,velocity);
    
    prevAcce = acce;
    prevVelocity = velocity;
    
   // NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
   // [prefs setFloat:velocity  forKey:@"velocity"];
    //[prefs synchronize];
}

- (void)didUpdateHeading {
    
    NSString *heading = [NSString stringWithFormat:@"%.2f", [[_sensorManager deviceAttitude] heading]];
    //convert object to data
    
    
    NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
    float zeroval = [prefs floatForKey:@"0"];
    float oneval = [prefs floatForKey:@"1"];
    float twoval = [prefs floatForKey:@"2"];
    float threeval = [prefs floatForKey:@"3"];
    
    
    if([heading integerValue] < 90){
        
        for (UIView *subview in [self.view subviews]) {
            if (subview.tag == 12) {
                [UIView beginAnimations:@"fade in" context:nil];
                [UIView setAnimationDuration:0.2];
                subview.alpha = zeroval;
                
                NSLog(@"90 %f",zeroval);
                [UIView commitAnimations];
                
            }
        }
        
        
    }
    else if([heading integerValue] < 180) {
        
        for (UIView *subview in [self.view subviews]) {
            if (subview.tag == 12) {
                [UIView beginAnimations:@"fade in" context:nil];
                
                [UIView setAnimationDuration:0.2];
                subview.alpha = oneval;
                [UIView commitAnimations];
                
            }
        }
        
    }
    else if([heading integerValue] < 270) {
        
        for (UIView *subview in [self.view subviews]) {
            if (subview.tag == 12) {
                [UIView beginAnimations:@"fade in" context:nil];
                
                [UIView setAnimationDuration:0.2];
                subview.alpha = twoval;
                
                
                [UIView commitAnimations];
                
            }
        }
        
        
    }
    else if([heading integerValue] < 360) {
        for (UIView *subview in [self.view subviews]) {
            if (subview.tag == 12) {
                [UIView beginAnimations:@"fade in" context:nil];
                
                [UIView setAnimationDuration:0.2];
                subview.alpha = threeval;
                [UIView commitAnimations];
            }
        }
        
    }
    
    
    
    
}

-(void)did {
    
    
    
    //NSLog(@"%@")
}
-(void)initializeCaptureSession
{
    
    // Attempt to initialize AVCaptureDevice with back camera
    NSArray *videoDevices = [AVCaptureDevice devicesWithMediaType:AVMediaTypeVideo];
    AVCaptureDevice *captureDevice = nil;
    for (AVCaptureDevice *device in videoDevices)
    {
        if (device.position == AVCaptureDevicePositionBack)
        {
            captureDevice = device;
            break;
        }
    }
    
    // If camera is accessible by capture session
    if(captureDevice)
    {
        
        // Allocate camera capture session
        cameraCaptureSession = [[AVCaptureSession alloc] init];
        cameraCaptureSession.sessionPreset = AVCaptureSessionPresetMedium;
        
        // Configure capture session input
        AVCaptureDeviceInput *videoIn = [AVCaptureDeviceInput deviceInputWithDevice:captureDevice error:nil];
        [cameraCaptureSession addInput:videoIn];
        
        // Configure capture session output
        AVCaptureVideoDataOutput *videoOut = [[AVCaptureVideoDataOutput alloc] init];
        [videoOut setAlwaysDiscardsLateVideoFrames:YES];
        [cameraCaptureSession addOutput:videoOut];
        
        // Bind preview layer to capture session data
        cameraPreviewLayer = [[AVCaptureVideoPreviewLayer alloc] initWithSession:cameraCaptureSession];
        
        CGRect layerRect = CGRectMake(0, 0, [[UIScreen mainScreen] applicationFrame].size.width, [[UIScreen mainScreen] applicationFrame].size.height + 20);
        // layerRect.size.height += 40;
        
        cameraPreviewLayer.bounds = [[UIScreen mainScreen] bounds];
        cameraPreviewLayer.position = CGPointMake(CGRectGetMidX(layerRect), CGRectGetMidY(layerRect));
        cameraPreviewLayer.videoGravity = AVLayerVideoGravityResizeAspectFill;
        
        // Add preview layer to UIView layer
        [self.view.layer addSublayer:cameraPreviewLayer];
        
        // Begin camera capture
        [cameraCaptureSession startRunning];
    }
    else // Camera is not accessible. Report and bail.
    {
        UIAlertView *alert = [[UIAlertView alloc]
                              initWithTitle:@"Camera Not Available"
                              message:@""
                              delegate:nil
                              cancelButtonTitle:@"Okay"
                              otherButtonTitles:nil];
        [alert show];
        
    }
}

-(IBAction)snap:(id)sender {
    
    NSString *heading = [NSString stringWithFormat:@"%.2f", [[_sensorManager deviceAttitude] heading]];
    //convert object to data
    CLLocation* l = [[_sensorManager deviceAttitude] location];
    CLLocationCoordinate2D c = [l coordinate];
    
    
    NSString *args2 =  [NSString stringWithFormat: @"[%.4f,%.4f,%.2f,%i]", c.latitude,c.longitude,l.horizontalAccuracy,heading.intValue];
    
    NSDictionary *dic = [[NSDictionary alloc] initWithObjectsAndKeys:
                         @"snap", @"action", args2, @"args", nil]; //nil to signify end of objects and keys.
    
    [_webSocket send:[dic JSONRepresentation]];
    
    //[self.navigationController popViewControllerAnimated:YES];
}

-(void)leave {
    [self.navigationController setNavigationBarHidden:NO animated:YES];
    
    [self.navigationController popViewControllerAnimated:YES];
    
}
#pragma mark - SRWebSocketDelegate

- (void)webSocketDidOpen:(SRWebSocket *)webSocket;
{
    NSLog(@"Websocket Connected");
    self.title = @"Connected!";
}

- (void)webSocket:(SRWebSocket *)webSocket didFailWithError:(NSError *)error;
{
    NSLog(@":( Websocket Failed With Error %@", error);
    
    self.title = @"Connection Failed! (see logs)";
    _webSocket = nil;
}

- (void)webSocket:(SRWebSocket *)webSocket didReceiveMessage:(id)message;
{
    store = [message JSONValue];
    NSLog(@"Received \"%@\"", [message JSONValue]);
    
    NSUserDefaults *prefs = [NSUserDefaults standardUserDefaults];
    
    NSDictionary *jsonDict = [message JSONValue];
    
    //NSLog(@"%@",[jsonDict objectForKey:@"args"]);
    valuescomp = [NSMutableArray arrayWithArray:[jsonDict objectForKey:@"args"]];
    
    if ([[[NSMutableArray arrayWithObject:[jsonDict objectForKey:@"action"]] objectAtIndex:0] isEqualToString:@"notify"])
    {    
        
        UIAlertView *alert = [[UIAlertView alloc]
                              initWithTitle:@"A GHOST HAS BEEN FOUND!"
                              message:@""
                              delegate:nil
                              cancelButtonTitle:@"Okay"
                              otherButtonTitles:nil];
        [alert show];
        [prefs setFloat:[[valuescomp objectAtIndex:0] floatValue] forKey:@"ghostlat"];
        [prefs setFloat:[[valuescomp objectAtIndex:1] floatValue] forKey:@"ghostlon"];
        [prefs setFloat:[[valuescomp objectAtIndex:2] floatValue] forKey:@"ghostheading"];
        [prefs setValue:@"someoneghost" forKey:@"ghostsource"];
        [[NSUserDefaults standardUserDefaults] synchronize];
        [self leave];
    }
    else if ([[[NSMutableArray arrayWithObject:[jsonDict objectForKey:@"action"]] objectAtIndex:0] isEqualToString:@"snap"])
    {    
        
        if ([[valuescomp objectAtIndex:0] floatValue]  == 0) {
            NSLog(@"NO GHOST");
            
        }
        else {
            NSLog(@"GHOST");
            UIAlertView *alert = [[UIAlertView alloc]
                                  initWithTitle:@"Nice! You found a ghost"
                                  message:@""
                                  delegate:nil
                                  cancelButtonTitle:@"Okay"
                                  otherButtonTitles:nil];
            [prefs setValue:@"myghost" forKey:@"ghostsource"];
            [prefs synchronize];
            [self leave];
            
            
            
            [alert show];
            
            
        }
        
    }
    else{
        
     //  store  = [NSString stringWithFormat:@"%@",[valuescomp objectAtIndex:0]];
        
        NSLog(@"VALUECOMP DOWN HERE %@",[valuescomp objectAtIndex:0]);
                
        
        // saving a Float
        NSLog(@"in the else");
        if([valuescomp objectAtIndex:0] != nil){
        [prefs setFloat:[[valuescomp objectAtIndex:0] floatValue] forKey:@"0"];
        [prefs setFloat:[[valuescomp objectAtIndex:1] floatValue] forKey:@"1"];
        [prefs setFloat:[[valuescomp objectAtIndex:2] floatValue] forKey:@"2"];
        [prefs setFloat:[[valuescomp objectAtIndex:3] floatValue] forKey:@"3"];
        [[NSUserDefaults standardUserDefaults] synchronize];
        }
    }
    
    
    /*
     //NSData *data = [[message JSONValue] dataUsingEncoding:NSUTF8StringEncoding];
     
     store = [message JSONValue];
     NSLog(@"Received \"%@\"", [message JSONValue]);
     
     
     id json = [NSJSONSerialization JSONObjectWithData:data options:0 error:nil];
     
     NSLog(@"%@", [json objectAtIndex:0] );
     NSError *jsonError = nil;
     NSLog(@"%@",[NSJSONSerialization JSONObjectWithData:message options:0 error:&jsonError]);
     
     
     */
    
    
    
    
}

- (void)webSocket:(SRWebSocket *)webSocket didCloseWithCode:(NSInteger)code reason:(NSString *)reason wasClean:(BOOL)wasClean;
{
    NSLog(@"WebSocket closed");
    self.title = @"Connection Closed! (see logs)";
    _webSocket = nil;
}

- (void)didReceiveMemoryWarning
{
    [super didReceiveMemoryWarning];
    // Dispose of any resources that can be recreated.
}
- (BOOL)shouldAutorotateToInterfaceOrientation:(UIInterfaceOrientation)toInterfaceOrientation;
{
    return NO;
}

@end