def identity_mtx():
    return [[1.0, 0.0, 0.0],[0.0, 1.0, 0.0]]

def inverse(((m00, m01, m02), (m10, m11, m12))):
    # TODO: improve inverse calculation
    m20 = 0
    m21 = 0
    m22 = 1
    det = m00*m11*m22 + m01*m12*m20 + m02*m10*m21 - m00*m12*m21 - m01*m10*m22 - m02*m11*m20;
    return [[float(m11*m22 - m12*m21)/det,
             float(m02*m21 - m01*m22)/det,
             float(m01*m12 - m02*m11)/det],
            [float(m12*m20 - m10*m22)/det,
             float(m00*m22 - m02*m20)/det,
             float(m02*m10 - m00*m12)/det
             ]]

def apply_transform_to_point(trans, pt):
    x = trans[0][0]*pt[0] + trans[0][1]*pt[1] + trans[0][2]
    y = trans[1][0]*pt[0] + trans[1][1]*pt[1] + trans[1][2]
    pt[0]=x
    pt[1]=y

def transform_mtx(width, height, (x,y), (a,b), (c,d)):
    a -= x
    b -= y
    c -= x
    d -= y
    return [[a / width, c / height, x], [b / width, d / height, y]]
