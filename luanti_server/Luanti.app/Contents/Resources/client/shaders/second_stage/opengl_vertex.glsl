#ifdef ENABLE_AUTO_EXPOSURE
#define exposureMap texture2

uniform sampler2D exposureMap;

varying float exposure;
#endif

#ifdef GL_ES
varying mediump vec2 varTexCoord;
#else
centroid varying vec2 varTexCoord;
#endif

void main(void)
{
#ifdef ENABLE_AUTO_EXPOSURE
	// value in the texture is on a logarithtmic scale
	exposure = texture2D(exposureMap, vec2(0.5)).r;
	exposure = pow(2., exposure);
#endif

	varTexCoord.st = inTexCoord0.st;
	gl_Position = inVertexPosition;
}
