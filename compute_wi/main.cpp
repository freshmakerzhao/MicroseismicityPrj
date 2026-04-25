#include<iostream>
#include<cmath>

using namespace std;
double sigma,E,K,lambda1,lambda2,xi; //sigma为单轴抗压强度；E为弹性模量；K为冲击模量指数 ；lambda1为峰后软化模量；lambda2为残余降模量；xi为残余强度系数；
// 采用希纳字母的英文单词代表该希纳字母;
double Ps,phi1,phi2;// Ps为待预警巷道的支护应力，phi1为塑性软化区的煤岩介质内摩擦角；phi2为破碎区的煤岩介质内摩擦角；
double q,m,alpha,beta_val,omega,rho_c;// 为简化计算式而定义的数据；
double P0,p0,pfcr,pcr;//p0为将待预警巷道等效为均质、连续且各向同性的圆形巷道后的巷道半径；pfcr为待预警巷道冲击地压发生的临界破碎区半径；pcr为临界软化区半径；
double Pcr,Pfcr,Pmcr;//Pcr为待预警巷道冲击地压发生的临界地应力；Pfcr为待预警巷道冲击地压发生时围岩破碎区对塑性软化区的作用应力；

double sanjiao(double phi)
{
	double a,b,num;
	a=1+sin(phi);
	b=1-sin(phi);
	num=a/b;
	return num;
}
//为计算q,m定义一个计算三角函数的函数sanjiao；
double pfcrhs(double a,double b,double c,double d,double e)//输入顺序为p0,Ps,q,alpha,beta_val;
{
	double x,y,num;
	x=b*(c-1);
	x=x+d;
	x=x/e;
	y=sqrt(x);
	num=a*y;
	return num;
}
//计算待预警巷道冲击地压发生的临界破碎区半径pfcr的函数；
double pcrhs(double a,double b,double c,double d,double e,double f,double g,double h)//输入顺序为p0,Ps,q,alpha,beta_val,xi,E,lambda1;
{
   double x,y,num;
   x=(b*(c-1)+d)/e;
   y=((1-f)*g)/h+1;
   x=sqrt(x);
   y=sqrt(y);
   num=a*x*y;
   return num;
 }
 //计算临界软化区半径pcr的函数
double alphahs(double a,double b,double c,double d,double e)//输入顺序为sigma,lambda1,lambda2,E,xi;
{
 	double x,y,z,num;
 	x=c/d;
 	y=(c*(1-e))/b+e;
 	z=x+y;
 	num=z*a;
 	return num;
 }
//计算alpha的函数
double betahs(double a,double b,double c,double d,double e)//输入顺序为sigma,lambda1,lambda2,E,xi;
{
	double x,y,z,num;
	x=c/d;
 	y=(c*(1-e))/b;
 	z=x+y;
 	num=z*a;
 	return num;
 }
//计算beta的函数
double  Pfcrhs(double a,double b,double c,double d,double e,double f)//输入顺序为Ps,pfcr,p0,q,alpha,beta_val;
{
	double x,y,z,num;
	double n1,n2;//用于表示幂函数的次方数
	n1=d-1;
	n2=d+1;
	double n,i;
	i=b/c;
	n=pow(i,n1);
	x=a*n;
	y=(e/(1-d))*(1-n);
	n=pow(i,n2);
	z=(f/(1+d))*(1-n);
	num=x+y+z;
	return num;
 }
//计算待预警巷道冲击地压发生时围岩破碎区对塑性软化区的作用应力Pfcr的函数；
int main ()
{
	sigma=5400;
	E=2580000;
	K=0.58;
	xi=0.28;
	lambda1=1496400;
	lambda2=16000;
	Ps=400;
	p0=2.37;
	phi1=0.5236;
	phi2=0.34;
	q=sanjiao(phi2);
	m=sanjiao(phi1);
	alpha=alphahs(sigma,lambda1,lambda2,E,xi);
    beta_val = betahs(sigma,lambda1,lambda2,E,xi);
	pcr=pcrhs(p0,Ps,q,alpha,beta_val,xi,E,lambda1);
	pfcr=pfcrhs(p0,Ps,q,alpha,beta_val);
	Pfcr=Pfcrhs(Ps,pfcr,p0,q,alpha,beta_val);
	double m_soft = m;
    double term1 = (m_soft + 1.0) / 2.0;
    double term2 = Pfcr / sigma + (1.0 + lambda1 / E) / (m_soft - 1.0);
    double base = 1.0 + (1.0 - xi) * E / lambda1;
    double exp1 = (m_soft - 1.0) / 2.0;
    double exp2 = (m_soft + 1.0) / 2.0;
    double part1 = term1 * term2 * pow(base, exp1);
    double part2 = (lambda1 / E) / 2.0 * pow(base, exp2);
    double part3 = (1.0 + lambda1 / E) / (m_soft - 1.0);
    double Pcr = sigma * (part1 - part2 - part3);
	double n1=0.89;  // 矩形巷道
	Pmcr=2*Pcr-(2*Pcr-sigma) / (m_soft+1.0);
	Pmcr=n1*Pmcr;
	cout << "input cai dong feng zhi ying li P0 (kPa): ";
    cin >> P0;
    cout << "input rao dong ying li bu jun yun die jia xi shu omega (0.75~0.95): ";
    cin >> omega;
    cout << "input mei yan mi du rho_c (kg/m^3): ";
    cin >> rho_c;
    double sigma_bmax=omega*(Pmcr-P0);   // 最大容许扰动应力 (kPa)
    double v_max=sqrt(sigma_bmax/(2.0*rho_c)); // 质点峰值速度 (m/s)
    cout<<"zui da rong xu rao dong ying li sigma_bmax = " <<sigma_bmax<<"kPa"<< endl;
    cout<<"dui ying zhi dian feng zhi su du v_max = "<<v_max <<"m/s"<< endl;
    double a_mc,b_mc;
    cout<<"input wei zhen xi tong xi shu a, b (lgE = a*M_L + b): ";
    cin>>a_mc>>b_mc;
    double exponent=(100.0*a_mc)/57.0;
    double inner=pow(10.0,2.05+57.0*b_mc/(100.0*a_mc))*v_max;
    double Q_R100_initial=pow(inner, exponent);
    cout << "zhen zhong ju 100m yu jing neng liang chu zhi Q_R100_initial = " << Q_R100_initial << " J" << endl;
    double Q_min_R100;
    cout << "input li shi wei zhen shi jian zhong yin qi chong ji de zui xiao deng xiao neng liang Q_min_R100 (J): ";
    cin >> Q_min_R100;
    double Q_R100_star = (Q_min_R100 < Q_R100_initial) ? Q_min_R100 : Q_R100_initial;
    double R_event,Q_event;
    cout << "wei zhen dan zhi yu jing neng liang biao zhun zhi Q_R100_star = " << Q_R100_star << " J" << endl;
    cout << "input dai ping gu wei zhen shi jian de zhen zhong ju R (m) and neng liang Q (J): ";
    cin >> R_event >> Q_event;
    // 将实际能量折算到震中距100m的等效能量
    double Q_event_R100 = Q_event * pow(10.0, (200.0 * a_mc - 100.0 * a_mc * log10(R_event)) / 57.0);
    double W_i = Q_event_R100 / Q_R100_star;
    cout << "gai wei zhen shi jian de deng xiao neng liang Q_event_R100 = " << Q_event_R100 << " J" << endl;
    cout << "chong ji wei xian dong tai xi shu W_i = " << W_i << endl;
    // ========== 步骤7：确定危险等级及建议措施 ==========
    if (W_i < 0.25) {
        cout << "chong ji wei xian deng ji: wu" << endl;
    } else if (W_i < 0.5) {
        cout << "chong ji wei xian deng ji: ruo" << endl;
    } else if (W_i < 0.75) {
        cout << "chong ji wei xian deng ji: zhong" << endl;
   } else {
        cout << "chong ji wei xian deng ji: qiang" << endl;
   }
	return 0;
}

