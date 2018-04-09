
def shrink_file( filenames=['user','business',"review"] , amount=[300 ,300,3000]):
    for ( name ,  count ) in zip( filenames , amount):
        result=[]
        with open("../{}.json".format(name),buffering=1000) as f :
            for data in f:
                if len( result ) <= count :
                    result.append( data )
        # obtain data 
        print ( len( result ))
        with open("../dataset/{}.json".format(name),'w') as f :
            for data in result:
                f.write( data )

if __name__ == '__main__':
    shrink_file() 