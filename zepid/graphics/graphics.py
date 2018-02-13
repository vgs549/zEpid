import warnings
import math 
import numpy as np
import pandas as pd
from scipy.stats import norm
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.genmod.families import family
from statsmodels.genmod.families import links
from statsmodels.nonparametric.smoothers_lowess import lowess
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

class effectmeasure_plot:
    '''Used to generate effect measure plots. effectmeasure plot accepts four list type objects.
    effectmeasure_plot is initialized with the associated names for each line, the point estimate, 
    the lower confidence limit, and the upper confidence limit.
    
    Plots will resemble the following form:
    
        _____________________________________________      Measure     % CI 
        |                                           |
    1   |        --------o-------                   |       x        n, 2n
        |                                           |
    2   |                   ----o----               |       w        m, 2m
        |                                           | 
        |___________________________________________|
        #           #           #           #
    
    
    
    The following functions (and their purposes) live within effectmeasure_plot
    
    labels(**kwargs)
        Used to change the labels in the plot, as well as the center and scale. Inputs are 
        keyword arguments
        KEYWORDS:
            -effectmeasure  + changes the effect measure label
            -conf_int       + changes the confidence interval label
            -scale          + changes the scale to either log or linear
            -center         + changes the reference line for the center
    
    colors(**kwargs)
        Used to change the color of points and lines. Also can change the shape of points.
        Valid colors and shapes for matplotlib are required. Inputs are keyword arguments
        KEYWORDS:
            -errorbarcolor  + changes the error bar colors
            -linecolor      + changes the color of the reference line
            -pointcolor     + changes the color of the points
            -pointshape     + changes the shape of points
    
    plot(t_adjuster=0.01,decimal=3,size=3)
        Generates the effect measure plot of the input lists according to the pre-specified 
        colors, shapes, and labels of the class object
        Arguments:
            -t_adjuster     + used to refine alignment of the table with the line graphs. 
                              When generate plots, trial and error for this value are usually
                              necessary
            -decimal        + number of decimal places to display in the table
            -size           + size of the plot to generate
    
    
    Below is an example of this function:
    
    >lab = ['One','Two'] #generating lists of data to plot
    >emm = [1.01,1.31]
    >lcl = ['0.90',1.01]
    >ucl = [1.11,1.53]
    >
    >x = effectmeasure_plot(lab,emm,lcl,ucl) #initializing effectmeasure_plot with the above lists
    >x.labels(effectmeasure='RR') #changing the table label to 'RR'
    >x.colors(pointcolor='r') #changing the point colors to red 
    >x.plot(t_adjuster=0.13) #generating the effect measure plot 

    '''
    def __init__(self,label,effect_measure,lcl,ucl):
        '''Initializes effectmeasure_plot with desired data to plot. All lists should be the same 
        length. If a blank space is desired in the plot, add an empty character object (' ') to 
        each list at the desired point.
        
        Inputs:
        
        label
            -list of labels to use for y-axis
        effect_measure
            -list of numbers for point estimates to plot. If point estimate has trailing zeroes, 
             input as a character object rather than a float
        lcl
            -list of numbers for upper confidence limits to plot. If point estimate has trailing 
             zeroes, input as a character object rather than a float
        ucl 
            -list of numbers for upper confidence limits to plot. If point estimate has 
             trailing zeroes, input as a character object rather than a float
        '''
        self.df = pd.DataFrame()
        self.df['study'] = label
        self.df['OR'] = effect_measure
        self.df['LCL'] = lcl
        self.df['UCL'] = ucl
        self.df['OR2'] = self.df['OR'].astype(str).astype(float)
        if ((all(isinstance(item,float) for item in lcl))&(all(isinstance(item,float) for item in effect_measure))):
            self.df['LCL_dif'] = self.df['OR'] - self.df['LCL']
        else:
            self.df['LCL_dif'] = (pd.to_numeric(self.df['OR'])) - (pd.to_numeric(self.df['LCL']))
        if ((all(isinstance(item,float) for item in ucl))&(all(isinstance(item,float) for item in effect_measure))):
            self.df['UCL_dif'] = self.df['UCL'] - self.df['OR']
        else:
            self.df['UCL_dif'] = (pd.to_numeric(self.df['UCL'])) - (pd.to_numeric(self.df['OR']))
        self.em = 'OR'
        self.ci = '95% CI'
        self.scale = 'log'
        self.center = 1
        self.errc = 'dimgrey'
        self.shape = 'd'
        self.pc = 'k'
        self.linec = 'gray'
    
    def labels(self,**kwargs):
        '''Function to change the labels of the outputted table. Additionally, the scale and reference
        value can be changed. 
        
        Accepts the following keyword arguments:
        
        effectmeasure  
            -changes the effect measure label
        conf_int       
            -changes the confidence interval label
        scale          
            -changes the scale to either log or linear
        center         
            -changes the reference line for the center
        '''
        if 'effectmeasure' in kwargs:
            self.em = kwargs['effectmeasure']
        if 'ci' in kwargs:
            self.ci = kwargs['conf_int'] 
        if 'scale' in kwargs:
            self.scale = kwargs['scale']
        if 'center' in kwargs:
            self.center = kwargs['center']
    
    def colors(self,**kwargs):
        '''Function to change colors and shapes. 
        
        Accepts the following keyword arguments:
        
        errorbarcolor  
            -changes the error bar colors
        linecolor      
            -changes the color of the reference line
        pointcolor     
            -changes the color of the points
        pointshape     
            -changes the shape of points
        '''
        if 'errorbarcolor' in kwargs:
            self.errc = kwargs['errorbarcolor']
        if 'pointshape' in kwargs:
            self.shape = kwargs['pointshape']
        if 'linecolor' in kwargs:
            self.linec = kwargs['linecolor']
        if 'pointcolor' in kwargs:
            self.pc = kwargs['pointcolor']
    
    def plot(self,t_adjuster=0.01,decimal=3,size=3):
        '''Generates the matplotlib effect measure plot with the default or specified attributes. 
        The following variables can be used to further fine-tune the effect measure plot
        
        t_adjuster     
            -used to refine alignment of the table with the line graphs. When generate plots, trial
             and error for this value are usually necessary. I haven't come up with an algorithm to
             determine this yet...
        decimal        
            -number of decimal places to display in the table
        size           
            -size of the plot to generate
        '''
        tval = []
        ytick = []
        for i in range(len(self.df)):
            if (np.isnan(self.df['OR2'][i])==False):
                if ((isinstance(self.df['OR'][i],float))&(isinstance(self.df['LCL'][i],float))&(isinstance(self.df['UCL'][i],float))):
                    tval.append([round(self.df['OR2'][i],decimal),('('+str(round(self.df['LCL'][i],decimal))+', '+str(round(self.df['UCL'][i],decimal))+')')])
                else:
                    tval.append([self.df['OR'][i],('('+str(self.df['LCL'][i])+', '+str(self.df['UCL'][i])+')')])
                ytick.append(i)
            else:
                tval.append([' ',' '])
                ytick.append(i)
        if (pd.to_numeric(self.df['UCL']).max() < 1):
            maxi = round(((pd.to_numeric(self.df['UCL'])).max() + 0.05),2) #setting x-axis maximum for UCL less than 1
        if ((pd.to_numeric(self.df['UCL']).max() < 9) & (pd.to_numeric(self.df['UCL']).max() >= 1)):
            maxi = round(((pd.to_numeric(self.df['UCL'])).max() + 1),0) #setting x-axis maximum for UCL less than 10
        if (pd.to_numeric(self.df['UCL']).max() > 9):
            maxi = round(((pd.to_numeric(self.df['UCL'])).max() + 10),0) #setting x-axis maximum for UCL less than 100
        if (pd.to_numeric(self.df['LCL']).min() > 0):
            mini = round(((pd.to_numeric(self.df['LCL'])).min() - 0.1),1) #setting x-axis minimum
        if (pd.to_numeric(self.df['LCL']).min() < 0):
            mini = round(((pd.to_numeric(self.df['LCL'])).min() - 0.05),2) #setting x-axis minimum
        plt.figure(figsize=(size*2,size*1)) #blank figure
        gspec = gridspec.GridSpec(1, 6) #sets up grid
        plot = plt.subplot(gspec[0, 0:4]) #plot of data
        tabl = plt.subplot(gspec[0, 4:]) # table of OR & CI 
        plot.set_ylim(-1,(len(self.df))) #spacing out y-axis properly
        if (self.scale=='log'):
            plot.set_xscale('log')
        plot.axvline(self.center,color=self.linec,zorder=1)
        plot.errorbar(self.df.OR2,self.df.index,xerr=[self.df.LCL_dif,self.df.UCL_dif],marker='None',zorder=2,ecolor=self.errc,elinewidth=(size/size),linewidth=0)
        plot.scatter(self.df.OR2,self.df.index,c=self.pc,s=(size*25),marker=self.shape,zorder=3,edgecolors='None')
        plot.xaxis.set_ticks_position('bottom')
        plot.yaxis.set_ticks_position('left')
        plot.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        plot.get_xaxis().set_minor_formatter(matplotlib.ticker.NullFormatter())
        plot.set_yticks(ytick)
        plot.set_xlim([mini,maxi])
        plot.set_xticks([mini,self.center,maxi])
        plot.set_xticklabels([mini,self.center,maxi])
        plot.set_yticklabels(self.df.study)
        plot.yaxis.set_ticks_position('none')
        plot.invert_yaxis() #invert y-axis to align values properly with table
        tb = tabl.table(cellText=tval,cellLoc='center',loc='right',colLabels=[self.em,self.ci],bbox=[0,t_adjuster,1,1])
        tabl.axis('off');tb.auto_set_font_size(False);tb.set_fontsize(12)
        for key,cell in tb.get_celld().items():
            cell.set_linewidth(0)
        plt.show()



def func_form_plot(df,outcome,var,f_form=None,outcome_type='binary',link_dist=None,ylims=None,loess_value=0.5,legend=True,model_results=True,loess=True,points=False):
    '''Creates a LOESS plot to aid in functional form assessment for continuous variables.
    Plots can be created for binary and continuous outcomes. Default options are set to create
    a functional form plot for a binary outcome. To convert to a continuous outcome, 
    outcome_type needs to be changed, in addition to the link_dist
    
    Returns a matplotlib graph with a LOESS line (dashed red-line), regression line (sold blue-line),
    and confidence interval (shaded blue)
    
    df:
        -dataframe that contains the variables of interest
    outcome:
        -Column name of the outcome variable of interest
    var:
        -Column name of the variable of interest for the functional form assessment
    f_form:
        -Regression equation of the functional form to assess. Default is None, which will produce
         a linear functional form. Input the regression equation as the variables of interest, separated
         by +. Example) 'var + var_sq'
    outcome_type:
        -Variable type of the outcome variable. Currently, only binary and continuous variables are
         supported. Default is binary
    link_dist:
        -Link and distribution for the GLM regression equation. Change this to any valid link and 
        distributions supported by statsmodels. Default is None, which conducts logistic regression
    ylims:
        -List object of length 2 that holds the upper and lower limits of the y-axis. Y-axis limits should be 
        specified when comparing multiple graphs. These need to be user-specified since the results between
        models and datasets can be so variable. Default is None, which returns the matplotlib y-axis of best fit.
    loess_value:
        -Fraction of observations to use to fit the LOESS curve. This will need to be changed iteratively
         to determine which percent works best for the data. Default is 0.5
    legend:
        -Turn the legend on or off. Default is True, displaying the legend in the graph 
    model_results:
        -Whether to produce the model results. Default is True, which provides model results
    loess:
        -Whether to plot the LOESS curve along with the functional form. Default is True
    points:
        -Whether to plot the data points, where size is relative to the number of observations. Default is False
    '''
    rf = df.copy()
    rf = rf.dropna().sort_values(by=[var,outcome]).reset_index()
    print('Warning: missing observations of model variables are dropped')
    print(int(len(df)-len(rf)),' observations were dropped from the functional form assessment')
    if f_form == None:
        f_form = var 
    else:
        pass 
    if link_dist == None:
        link_dist = sm.families.family.Binomial(sm.families.links.logit)
    else:
        pass 
    if (loess == True) | (points == True):
        if outcome_type=='binary':
            djm = smf.glm(outcome+'~ C('+var+')',rf,family=link_dist).fit()
            djf = djm.get_prediction(rf).summary_frame()        
            dj = pd.concat([rf,djf],axis=1)
            dj.sort_values(var,inplace=True)
            if points == True:
                pf = dj.groupby(by=[var,'mean']).count().reset_index()
            if loess == True:
                yl = lowess(list(dj['mean']),list(dj[var]),frac=loess_value)
                lowess_x = list(zip(*yl))[0]
                lowess_y = list(zip(*yl))[1]
        elif outcome_type=='continuous':
            if points == True:
                pf = rf.groupby(by=[var,outcome]).count().reset_index()
            if loess == True:
                yl = lowess(list(rf[outcome]),list(rf[var]),frac=loess_value)
                lowess_x = list(zip(*yl))[0]
                lowess_y = list(zip(*yl))[1]
        else:
            raise ValueError('Functional form assessment only supports binary or continuous outcomes currently')
    ffm = smf.glm(outcome+'~ '+f_form,rf,family=link_dist).fit()
    if model_results==True:
        print(ffm.summary())
        print('AIC: ',ffm.aic)
        print('BIC: ',ffm.bic)
    fff = ffm.get_prediction(rf).summary_frame()
    ff = pd.concat([rf,fff],axis=1)
    ff.sort_values(var,inplace=True)
    if points == True:
        if outcome_type == 'continuous':
            plt.scatter(pf[var],pf[outcome],s=[ 100*(n/max(pf[var])) for n in pf[var]],color='gray',label='Data point')
        else:
            plt.scatter(pf[var],pf['mean'],s=[100*(n/max(pf[var])) for n in pf[var]],color='gray',label='Data point')
    plt.fill_between(ff[var],ff['mean_ci_upper'],ff['mean_ci_lower'],alpha=0.1,color='blue',label='95% CI')
    plt.plot(ff[var],ff['mean'],'-',color='blue',label='Regression')
    if loess == True:
        plt.plot(lowess_x,lowess_y,'--',color='red',linewidth=1,label='LOESS')  
    plt.xlabel(var)
    if outcome_type=='binary':
        plt.ylabel('Probability')
    else:
        plt.ylabel(outcome)
    if legend == True:
        plt.legend()
    plt.ylim(ylims)
    plt.show()


